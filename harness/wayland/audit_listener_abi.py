#!/usr/bin/env python3
"""Audit Box86 Wayland listener callbacks against generated protocol headers.

The five accepted omissions are events newer than the interface versions that
Wine 11 binds in this port. Any signature mismatch, additional omission or
change to that exact allow-list fails closed.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
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

# The exact listener classes installed by Wine 11's winewayland driver in this
# port.  Requiring these names independently of the supplied header set keeps a
# missing protocol header from silently reducing coverage to an intersection.
REQUIRED_WINE_LISTENERS = {
    "wl_buffer_listener",
    "wl_data_device_listener",
    "wl_data_offer_listener",
    "wl_data_source_listener",
    "wl_keyboard_listener",
    "wl_output_listener",
    "wl_pointer_listener",
    "wl_registry_listener",
    "wl_seat_listener",
    "xdg_surface_listener",
    "xdg_toplevel_listener",
    "xdg_wm_base_listener",
    "zwlr_data_control_device_v1_listener",
    "zwlr_data_control_offer_v1_listener",
    "zwlr_data_control_source_v1_listener",
    "zwp_relative_pointer_v1_listener",
    "zwp_text_input_v3_listener",
    "zxdg_output_v1_listener",
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


@dataclass(frozen=True)
class ProtocolCallback:
    name: str
    signature: str


@dataclass(frozen=True)
class Box86Callback:
    name: str
    signature: str
    format_string: str | None


@dataclass(frozen=True)
class Box86Listener:
    callbacks: tuple[Box86Callback, ...]
    initializer: tuple[str, ...]


def protocol_listeners(paths: list[Path]) -> dict[str, tuple[ProtocolCallback, ...]]:
    result: dict[str, tuple[ProtocolCallback, ...]] = {}
    for path in paths:
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(
            r"struct\s+(\w+_listener)\s*\{(.*?)\n\};", source, re.S
        ):
            listener, body = match.groups()
            callbacks = []
            for callback in re.finditer(
                r"void\s*\(\*(\w+)\)\s*\((.*?)\);", body, re.S
            ):
                callbacks.append(
                    ProtocolCallback(
                        callback.group(1), parameter_signature(callback.group(2))
                    )
                )
            parsed = tuple(callbacks)
            previous = result.get(listener)
            if previous is not None and previous != parsed:
                raise ValueError(
                    f"conflicting protocol definitions for {listener}"
                )
            result[listener] = parsed
    return result


def box86_listeners(path: Path) -> dict[str, Box86Listener]:
    source = path.read_text(encoding="utf-8")
    result: dict[str, Box86Listener] = {}
    for match in re.finditer(
        r"typedef struct my_(\w+_listener)_s\s*\{(.*?)\}\s*my_\1_t;", source, re.S
    ):
        listener, body = match.groups()
        callbacks = []
        for field in re.findall(r"uintptr_t\s+(\w+)\s*;", body):
            function = re.search(
                r"static void my_%s_%s_##A\s*\((.*?)\)\s*\\?\s*\{(.*?)\}"
                % (re.escape(listener), re.escape(field)),
                source[match.end() :],
                re.S,
            )
            if not function:
                callbacks.append(Box86Callback(field, "missing", None))
                continue
            format_match = re.search(
                r'RunFunctionFmt\([^;]*?"([^"]+)"', function.group(2), re.S
            )
            callbacks.append(
                Box86Callback(
                    field,
                    parameter_signature(function.group(1)),
                    format_match.group(1) if format_match else None,
                )
            )

        initializer_match = re.search(
            r"static\s+my_%s_t\s+my_%s_fct_##A\s*=\s*\{(.*?)\};"
            % (re.escape(listener), re.escape(listener)),
            source[match.end() :],
            re.S,
        )
        initializer = ()
        if initializer_match:
            initializer = tuple(
                re.findall(
                    r"my_%s_(\w+)_##A" % re.escape(listener),
                    initializer_match.group(1),
                )
            )
        result[listener] = Box86Listener(tuple(callbacks), initializer)
    return result


def version_gated_callback(listener: str, callback: ProtocolCallback) -> bool:
    return (
        listener,
        callback.name,
        callback.signature,
        "missing",
    ) in VERSION_GATED_OMISSIONS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("box86_source", type=Path)
    parser.add_argument("protocol_headers", type=Path, nargs="+")
    args = parser.parse_args()

    protocol = protocol_listeners(args.protocol_headers)
    box86 = box86_listeners(args.box86_source)
    common = set(protocol) & set(box86)
    observed: set[tuple[str, str, str, str]] = set()
    errors: list[str] = []

    for listener in sorted(REQUIRED_WINE_LISTENERS - set(protocol)):
        errors.append(
            f"ERROR required Wine listener missing from protocol headers: {listener}"
        )
    for listener in sorted(REQUIRED_WINE_LISTENERS - set(box86)):
        errors.append(
            f"ERROR required Wine listener missing from Box86: {listener}"
        )

    for listener in sorted(common):
        expected_callbacks = protocol[listener]
        actual_listener = box86[listener]
        expected = {callback.name: callback.signature for callback in expected_callbacks}
        actual = {
            callback.name: callback.signature
            for callback in actual_listener.callbacks
        }
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

        projected_order = tuple(
            callback.name
            for callback in expected_callbacks
            if not version_gated_callback(listener, callback)
        )
        field_order = tuple(
            callback.name for callback in actual_listener.callbacks
        )
        if field_order != projected_order:
            errors.append(
                f"ERROR {listener} field order protocol={projected_order} "
                f"box={field_order}"
            )
        if actual_listener.initializer != field_order:
            errors.append(
                f"ERROR {listener} initializer order fields={field_order} "
                f"initializer={actual_listener.initializer}"
            )
        for callback in actual_listener.callbacks:
            if callback.format_string != callback.signature:
                errors.append(
                    f"ERROR {listener}.{callback.name} RunFunctionFmt="
                    f"{callback.format_string or 'missing'} "
                    f"parameters={callback.signature}"
                )

    missing_expected = VERSION_GATED_OMISSIONS - observed
    unexpected = observed - VERSION_GATED_OMISSIONS
    text_input_protocol = {
        callback.name: callback.signature
        for callback in protocol.get("zwp_text_input_v3_listener", ())
    }
    text_input_box = {
        callback.name: callback.signature
        for callback in box86.get(
            "zwp_text_input_v3_listener", Box86Listener((), ())
        ).callbacks
    }
    text_input_ok = (
        text_input_protocol.get("delete_surrounding_text")
        == text_input_box.get("delete_surrounding_text")
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
    for error in errors:
        print(error)

    passed = not unexpected and not missing_expected and text_input_ok and not errors
    print(
        f"compared_listeners={len(common)} "
        f"version_gated={len(observed & VERSION_GATED_OMISSIONS)} "
        f"unexpected={len(unexpected)} result={'PASS' if passed else 'FAIL'}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
