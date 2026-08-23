#!/usr/bin/env python3
"""Read the bounded Box86 history for production win32u's display_lock.

The v1 ring answered "is this thread waiting on a mutex it already owns" -- owner
== tid with lock == 2 -- and that is where FINALPLAY13 stopped.  It is not enough
to fix anything: a recursive ATTEMPT and an ordinary contended ATTEMPT produce the
same record, and the sixteen-word stack window ran out about two frames past the
pthread wrapper, so the win32u function that took the lock FIRST was never named.

v2 carries the missing half.  Each record now names the acquisition the same
thread has not released yet (owner_acquire_seq) and hashes its call chain, and the
window is 64 words.  So this prints the pair -- the acquisition that is still
standing, and the call that walked back in -- which is the thing a surgical
_locked()/_nolock() split needs and a recursive mutex would paper over.

Both versions are read, because the rollback binaries carry v1.
"""

import argparse
import pathlib
import re
import struct
import subprocess


MAGIC = 0x314C444D  # MDL1
HEADER = struct.Struct("<10I")
EVENTS = {1: "ATTEMPT", 2: "ACQUIRED", 3: "RELEASED"}
# Fixed words before stack[], per version.  v2 inserts owner_acquire_seq and
# chain_hash between result and stack.
FIXED_WORDS = {1: 9, 2: 11}


def symbol_value(path, name):
    output = subprocess.check_output(["readelf", "-Ws", path], text=True)
    values = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[-1] == name and fields[6] != "UND":
            values.append(int(fields[1], 16))
    if not values:
        raise RuntimeError(f"symbol {name!r} not found in {path}")
    if len(set(values)) != 1:
        raise RuntimeError(f"symbol {name!r} has conflicting values in {path}")
    return values[0]


def elf_type(path):
    output = subprocess.check_output(["readelf", "-h", path], text=True)
    match = re.search(r"^\s*Type:\s+(\S+)", output, re.MULTILINE)
    if not match:
        raise RuntimeError(f"cannot read ELF type from {path}")
    return match.group(1)


def mappings(pid, path):
    resolved = str(pathlib.Path(path).resolve())
    found = []
    for line in pathlib.Path(f"/proc/{pid}/maps").read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        mapped = fields[-1].removesuffix(" (deleted)")
        try:
            same = str(pathlib.Path(mapped).resolve()) == resolved
        except OSError:
            same = mapped == resolved
        if same:
            start, end = (int(value, 16) for value in fields[0].split("-", 1))
            found.append((start, end, int(fields[2], 16)))
    if not found:
        raise RuntimeError(f"{path} is not mapped in pid {pid}")
    return found


def mapped_base(pid, path):
    bases = {start - offset for start, _end, offset in mappings(pid, path)}
    if len(bases) != 1:
        raise RuntimeError(f"inconsistent load bases for {path}: {sorted(bases)}")
    return bases.pop()


def runtime_address(pid, path, symbol):
    value = symbol_value(path, symbol)
    return value if elf_type(path) == "EXEC" else mapped_base(pid, path) + value


def read_exact(mem, address, size):
    mem.seek(address)
    data = mem.read(size)
    if len(data) != size:
        raise RuntimeError(f"short /proc/PID/mem read at {address:#x}")
    return data


def read_stable(mem, address, size):
    for _ in range(8):
        first = read_exact(mem, address, size)
        second = read_exact(mem, address, size)
        if first == second:
            return first
    raise RuntimeError("history changed throughout the bounded read")


def addr2line(path, rvas):
    if not rvas:
        return {}
    ordered = sorted(rvas)
    output = subprocess.check_output(
        ["addr2line", "-e", path, "-f", "-C", *[hex(value) for value in ordered]], text=True
    ).splitlines()
    result = {}
    for index, rva in enumerate(ordered):
        function = output[2 * index] if 2 * index < len(output) else "??"
        location = output[2 * index + 1] if 2 * index + 1 < len(output) else "??:0"
        result[rva] = f"{function} ({location})"
    return result


class Record:
    """One ring entry, with the version differences already flattened away."""

    def __init__(self, words, version):
        fixed = FIXED_WORDS[version]
        (self.sequence, self.tid, self.event, self.mutex,
         self.caller, self.stack_pointer, self.lock, self.owner,
         self.result) = words[:9]
        if version >= 2:
            self.owner_acquire_seq, self.chain_hash = words[9], words[10]
        else:
            self.owner_acquire_seq, self.chain_hash = 0, 0
        self.stack = words[fixed:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--box86", default="/usr/bin/box86")
    parser.add_argument("--win32u", default="/usr/lib/wine/i386-unix/win32u.so")
    args = parser.parse_args()

    history_address = runtime_address(args.pid, args.box86, "mgs2_display_lock_history")
    with open(f"/proc/{args.pid}/mem", "rb", buffering=0) as mem:
        header = HEADER.unpack(read_exact(mem, history_address, HEADER.size))
        magic, version, size_words, signature = header[:4]
        if magic != MAGIC or signature != (~MAGIC & 0xFFFFFFFF):
            raise RuntimeError(f"bad history header: {header[:4]}")
        if version not in FIXED_WORDS:
            raise RuntimeError(f"history version {version} is not one this reader knows")
        capacity, record_words = header[5], header[6]
        stack_words = record_words - FIXED_WORDS[version]
        if stack_words <= 0 or HEADER.size // 4 + capacity * record_words != size_words:
            raise RuntimeError(
                f"bad history layout: capacity={capacity} record_words={record_words} "
                f"size_words={size_words}")
        record_struct = struct.Struct(f"<{record_words}I")
        data = read_stable(mem, history_address, size_words * 4)

    win32u_base = mapped_base(args.pid, args.win32u)
    win32u_maps = mappings(args.pid, args.win32u)
    display_address = win32u_base + symbol_value(args.win32u, "display_lock")
    session_address = win32u_base + symbol_value(args.win32u, "session_lock")
    target, target_caller = header[8], header[9]
    print(f"history @ {history_address:#x}: v{version} enabled={header[4]} writes={header[7]} "
          f"capacity={capacity} stack_words={stack_words}")
    print(f"win32u base {win32u_base:#x}: display_lock={display_address:#x} "
          f"session_lock={session_address:#x}")
    print(f"captured target={target:#x} caller={target_caller:#x}")
    if target:
        if target != display_address:
            raise RuntimeError(f"captured target {target:#x} is not display_lock {display_address:#x}")
        print("identity: MATCH display_lock; session_lock is excluded")
    else:
        print("identity: target call site has not executed yet")
    if version < 2:
        print("note: v1 ring -- no owner_acquire_seq, so a recursive ATTEMPT cannot be")
        print("      distinguished from ordinary contention and the first acquirer is unnamed")

    def in_win32u(value):
        return any(start <= value < end for start, end, _offset in win32u_maps)

    records = []
    win32u_addresses = set()
    for slot in range(capacity):
        words = record_struct.unpack_from(data, HEADER.size + slot * record_struct.size)
        if not words[0]:
            continue
        record = Record(words, version)
        records.append(record)
        for value in (record.caller, *record.stack):
            if in_win32u(value):
                win32u_addresses.add(value - win32u_base)
    records.sort(key=lambda item: item.sequence)
    by_sequence = {record.sequence: record for record in records}
    symbols = addr2line(args.win32u, win32u_addresses)

    def chain_lines(record, indent):
        items = []
        for offset, value in enumerate(record.stack):
            rva = value - win32u_base
            if rva in symbols:
                items.append(f"{indent}  esp+{offset * 4:<4d} {value:#x} = win32u+{rva:#x} "
                             f"{symbols[rva]}")
        return items

    self_waits = 0
    recursive = []
    for record in records:
        caller_rva = record.caller - win32u_base if in_win32u(record.caller) else None
        caller_text = (f" win32u+{caller_rva:#x} {symbols.get(caller_rva, '')}"
                       if caller_rva is not None else "")
        flags = ""
        if record.event == 1 and record.lock == 2 and record.owner == record.tid:
            self_waits += 1
            flags += " SELF-WAIT"
        held = by_sequence.get(record.owner_acquire_seq)
        if record.event == 1 and record.owner_acquire_seq:
            # The verdict this reader exists for.  The thread is asking for a
            # lock it is recorded as still holding, and both call chains are here.
            flags += f" RECURSIVE, standing on ACQUIRED #{record.owner_acquire_seq}"
            if held is None:
                flags += " (aged out of the ring)"
            recursive.append(record)
        print(f"#{record.sequence:<8d} tid={record.tid:<6d} {EVENTS.get(record.event, str(record.event)):<8s} "
              f"mutex={record.mutex:#x} lock={record.lock} owner={record.owner} "
              f"result={record.result:#x} chain={record.chain_hash:#010x} "
              f"eip={record.caller:#x}{caller_text}{flags}")
        for line in chain_lines(record, "        "):
            print(line)
        if record.event == 1 and record.owner_acquire_seq and held is not None:
            print(f"        --- still-held ACQUIRED #{held.sequence} took it at "
                  f"eip={held.caller:#x}, chain={held.chain_hash:#010x} ---")
            for line in chain_lines(held, "        "):
                print(line)

    print(f"verdict witness: self_wait_attempts={self_waits} recursive_attempts={len(recursive)}")
    if recursive:
        print("The pair above IS the fix site: split the function that appears in the")
        print("RECURSIVE chain but not in the still-held one into a _locked() variant and")
        print("call that from inside the lock. Do not make display_lock recursive -- the")
        print("hang becomes a read of gpus/sources/monitors while they are half-rebuilt.")
    elif version >= 2:
        print("No recursive attempt in the ring. Either the freeze is not this, or the")
        print("chain is longer than the ring: check whether writes exceeds capacity.")


if __name__ == "__main__":
    main()
