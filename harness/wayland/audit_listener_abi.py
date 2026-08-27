#!/usr/bin/env python3
"""Audit Box86 Wayland listener callbacks against generated protocol headers.

The five accepted omissions are events newer than the interface versions that
Wine 11 binds in this port. Any signature mismatch, additional omission or
change to that exact allow-list fails closed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


VERSION_GATED_OMISSIONS = {
    ("wl_surface_listener", "preferred_buffer_scale", "ppi", "missing"),
    ("wl_surface_listener", "preferred_buffer_transform", "ppu", "missing"),
    ("wl_touch_listener", "orientation", "ppii", "missing"),
    ("wl_touch_listener", "shape", "ppiii", "missing"),
    (
        "zwlr_data_control_device_v1_listener",
        "primary_selection",
        "ppp",
        "missing",
    ),
}


def parameter_signature(parameters: str) -> str:
    result = ""
    for parameter in parameters.split(","):
        parameter = re.sub(r"/\*.*?\*/", "", parameter, flags=re.S).strip()
        if not parameter or parameter == "void":
            continue
        if "*" in parameter:
            result += "p"
        elif "uint32_t" in parameter:
            result += "u"
        elif (
            "int32_t" in parameter
            or "wl_fixed_t" in parameter
            or re.search(r"\bint\b", parameter)
        ):
            result += "i"
        else:
            result += "?"
    return result


def protocol_listeners(paths: list[Path]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for path in paths:
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(
            r"struct\s+(\w+_listener)\s*\{(.*?)\n\};", source, re.S
        ):
            listener, body = match.groups()
            callbacks = {}
            for callback in re.finditer(
                r"void\s*\(\*(\w+)\)\s*\((.*?)\);", body, re.S
            ):
                callbacks[callback.group(1)] = parameter_signature(callback.group(2))
            result[listener] = callbacks
    return result


def box86_listeners(path: Path) -> dict[str, dict[str, str]]:
    source = path.read_text(encoding="utf-8")
    result: dict[str, dict[str, str]] = {}
    for match in re.finditer(
        r"typedef struct my_(\w+_listener)_s\s*\{(.*?)\}\s*my_\1_t;", source, re.S
    ):
        listener, body = match.groups()
        callbacks = {}
        for field in re.findall(r"uintptr_t\s+(\w+)\s*;", body):
            function = re.search(
                r"static void my_%s_%s_##A\s*\((.*?)\)"
                % (re.escape(listener), re.escape(field)),
                source[match.end() :],
                re.S,
            )
            if function:
                callbacks[field] = parameter_signature(function.group(1))
        result[listener] = callbacks
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("box86_source", type=Path)
    parser.add_argument("protocol_headers", type=Path, nargs="+")
    args = parser.parse_args()

    protocol = protocol_listeners(args.protocol_headers)
    box86 = box86_listeners(args.box86_source)
    common = set(protocol) & set(box86)
    observed: set[tuple[str, str, str, str]] = set()

    for listener in sorted(common):
        expected = protocol[listener]
        actual = box86[listener]
        for callback in sorted(set(expected) | set(actual)):
            wanted = expected.get(callback, "missing")
            got = actual.get(callback, "missing")
            if wanted == got:
                continue
            mismatch = (listener, callback, wanted, got)
            observed.add(mismatch)
            disposition = (
                "VERSION_GATED" if mismatch in VERSION_GATED_OMISSIONS else "ERROR"
            )
            print(
                f"{disposition} {listener}.{callback} "
                f"protocol={wanted} box={got}"
            )

    missing_expected = VERSION_GATED_OMISSIONS - observed
    unexpected = observed - VERSION_GATED_OMISSIONS
    text_input_ok = (
        protocol.get("zwp_text_input_v3_listener", {}).get(
            "delete_surrounding_text"
        )
        == box86.get("zwp_text_input_v3_listener", {}).get(
            "delete_surrounding_text"
        )
        == "ppuu"
    )

    if missing_expected:
        for listener, callback, wanted, got in sorted(missing_expected):
            print(
                f"ERROR expected allow-list entry absent: {listener}.{callback} "
                f"protocol={wanted} box={got}"
            )
    if not text_input_ok:
        print("ERROR zwp_text_input_v3.delete_surrounding_text is not exact ppuu")

    passed = not unexpected and not missing_expected and text_input_ok
    print(
        f"compared_listeners={len(common)} "
        f"version_gated={len(observed & VERSION_GATED_OMISSIONS)} "
        f"unexpected={len(unexpected)} result={'PASS' if passed else 'FAIL'}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
