#!/usr/bin/env python3
"""Read the bounded Box86 history for production win32u's display_lock."""

import argparse
import pathlib
import re
import struct
import subprocess


MAGIC = 0x314C444D  # MDL1
CAPACITY = 256
STACK_WORDS = 16
HEADER = struct.Struct("<10I")
RECORD = struct.Struct("<25I")
EVENTS = {1: "ATTEMPT", 2: "ACQUIRED", 3: "RELEASED"}


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--box86", default="/usr/bin/box86")
    parser.add_argument("--win32u", default="/usr/lib/wine/i386-unix/win32u.so")
    args = parser.parse_args()

    history_address = runtime_address(args.pid, args.box86, "mgs2_display_lock_history")
    size = HEADER.size + CAPACITY * RECORD.size
    with open(f"/proc/{args.pid}/mem", "rb", buffering=0) as mem:
        data = read_stable(mem, history_address, size)

    header = HEADER.unpack_from(data)
    expected_words = size // 4
    if header[:4] != (MAGIC, 1, expected_words, (~MAGIC & 0xFFFFFFFF)):
        raise RuntimeError(f"bad history header: {header[:4]}")
    if header[5:7] != (CAPACITY, RECORD.size // 4):
        raise RuntimeError(f"bad history layout: capacity={header[5]} words={header[6]}")

    win32u_base = mapped_base(args.pid, args.win32u)
    win32u_maps = mappings(args.pid, args.win32u)
    display_address = win32u_base + symbol_value(args.win32u, "display_lock")
    session_address = win32u_base + symbol_value(args.win32u, "session_lock")
    target, target_caller = header[8], header[9]
    print(f"history @ {history_address:#x}: enabled={header[4]} writes={header[7]}")
    print(f"win32u base {win32u_base:#x}: display_lock={display_address:#x} session_lock={session_address:#x}")
    print(f"captured target={target:#x} caller={target_caller:#x}")
    if target:
        if target != display_address:
            raise RuntimeError(f"captured target {target:#x} is not display_lock {display_address:#x}")
        print("identity: MATCH display_lock; session_lock is excluded")
    else:
        print("identity: target call site has not executed yet")

    records = []
    win32u_addresses = set()
    for slot in range(CAPACITY):
        record = RECORD.unpack_from(data, HEADER.size + slot * RECORD.size)
        if not record[0]:
            continue
        records.append(record)
        for value in (record[4], *record[9:]):
            if any(start <= value < end for start, end, _offset in win32u_maps):
                win32u_addresses.add(value - win32u_base)
    records.sort(key=lambda item: item[0])
    if len(records) > CAPACITY:
        records = records[-CAPACITY:]
    symbols = addr2line(args.win32u, win32u_addresses)

    self_waits = 0
    for record in records:
        sequence, tid, event, mutex, caller, stack_pointer, lock, owner, result = record[:9]
        suffix = " SELF-WAIT" if event == 1 and lock == 2 and owner == tid else ""
        if suffix:
            self_waits += 1
        caller_rva = caller - win32u_base if any(start <= caller < end for start, end, _ in win32u_maps) else None
        caller_text = f" win32u+{caller_rva:#x} {symbols.get(caller_rva, '')}" if caller_rva is not None else ""
        print(f"{sequence:8d} tid={tid:<6d} {EVENTS.get(event, str(event)):<8s} "
              f"mutex={mutex:#x} lock={lock} owner={owner} result={result:#x} "
              f"eip={caller:#x}{caller_text}{suffix}")
        stack_items = []
        for value in record[9:]:
            rva = value - win32u_base
            if rva in symbols:
                stack_items.append(f"{value:#x}=win32u+{rva:#x} {symbols[rva]}")
        if stack_items:
            print(f"         esp={stack_pointer:#x}: " + " | ".join(stack_items))
    print(f"verdict witness: self_wait_attempts={self_waits}")


if __name__ == "__main__":
    main()
