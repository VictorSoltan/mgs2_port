#!/usr/bin/env python3
"""Fail-closed regressions for the Wayland listener ABI auditor."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from wayland.audit_listener_abi import (
    REQUIRED_WINE_LISTENERS,
    VERSION_GATED_OMISSIONS,
)


ROOT = Path(__file__).resolve().parent.parent
AUDITOR = ROOT / "harness" / "wayland" / "audit_listener_abi.py"


def parameters(signature: str) -> str:
    types = {"p": "void *", "u": "uint32_t ", "i": "int32_t "}
    return ", ".join(types[kind] + f"a{index}" for index, kind in enumerate(signature))


def callback_set(listener: str) -> list[tuple[str, str]]:
    if listener == "zwp_text_input_v3_listener":
        return [("delete_surrounding_text", "ppuu")]
    if listener == "zwlr_data_control_device_v1_listener":
        return [
            ("data_offer", "ppp"),
            ("selection", "ppp"),
            ("finished", "pp"),
            ("primary_selection", "ppp"),
        ]
    if listener == "wl_surface_listener":
        return [
            ("enter", "ppp"),
            ("preferred_buffer_scale", "ppi"),
            ("preferred_buffer_transform", "ppu"),
        ]
    if listener == "wl_touch_listener":
        return [
            ("down", "ppu"),
            ("shape", "ppiii"),
            ("orientation", "ppii"),
        ]
    return [("event", "pp")]


def write_fixture(
    directory: Path,
    *,
    omit_protocol: str | None = None,
    swap_fields: str | None = None,
    swap_initializer: str | None = None,
    bad_format: tuple[str, str] | None = None,
) -> tuple[Path, Path]:
    listener_names = sorted(
        REQUIRED_WINE_LISTENERS
        | {entry[0] for entry in VERSION_GATED_OMISSIONS}
    )
    protocol_lines = []
    box_lines = []

    for listener in listener_names:
        callbacks = callback_set(listener)
        if listener != omit_protocol:
            protocol_lines.append(f"struct {listener} {{")
            for name, signature in callbacks:
                protocol_lines.append(
                    f"    void (*{name})({parameters(signature)});"
                )
            protocol_lines.append("};")

        active = [
            callback
            for callback in callbacks
            if (listener, callback[0], callback[1], "missing")
            not in VERSION_GATED_OMISSIONS
        ]
        fields = list(active)
        if listener == swap_fields:
            fields.reverse()
        box_lines.append(f"typedef struct my_{listener}_s {{")
        for name, _signature in fields:
            box_lines.append(f"    uintptr_t {name};")
        box_lines.append(f"}} my_{listener}_t;")
        box_lines.append("#define GO(A) \\")
        for index, (name, signature) in enumerate(fields):
            separator = " \\" if index + 1 < len(fields) else ""
            format_string = signature
            if bad_format == (listener, name):
                format_string = signature[:-1] or "p"
            arguments = ", ".join(f"a{i}" for i in range(len(signature)))
            box_lines.extend(
                [
                    f"static void my_{listener}_{name}_##A({parameters(signature)}) \\",
                    "{ \\",
                    f"RunFunctionFmt(ref_{listener}_##A->{name}, \"{format_string}\", {arguments}); \\",
                    "}" + separator,
                ]
            )
        initializer = [name for name, _signature in fields]
        if listener == swap_initializer:
            initializer.reverse()
        box_lines.append(
            f"static my_{listener}_t my_{listener}_fct_##A = {{"
        )
        for name in initializer:
            box_lines.append(f"    (uintptr_t)my_{listener}_{name}_##A,")
        box_lines.append("};")

    protocol = directory / "protocol.h"
    box = directory / "wrappedwaylandclient.c"
    protocol.write_text("\n".join(protocol_lines) + "\n", encoding="utf-8")
    box.write_text("\n".join(box_lines) + "\n", encoding="utf-8")
    return box, protocol


def run_fixture(**kwargs: object) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="mgs2-wayland-audit-") as name:
        box, protocol = write_fixture(Path(name), **kwargs)
        return subprocess.run(
            ["python3", str(AUDITOR), str(box), str(protocol)],
            text=True,
            capture_output=True,
            check=False,
        )


def require_failure(result: subprocess.CompletedProcess[str], marker: str) -> None:
    assert result.returncode != 0, result.stdout + result.stderr
    assert marker in result.stdout, result.stdout + result.stderr


def main() -> None:
    baseline = run_fixture()
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    assert "version_gated=5 unexpected=0 result=PASS" in baseline.stdout

    require_failure(
        run_fixture(swap_fields="zwlr_data_control_device_v1_listener"),
        "zwlr_data_control_device_v1_listener field order",
    )
    require_failure(
        run_fixture(swap_initializer="zwlr_data_control_device_v1_listener"),
        "zwlr_data_control_device_v1_listener initializer order",
    )
    require_failure(
        run_fixture(bad_format=("wl_data_offer_listener", "event")),
        "wl_data_offer_listener.event RunFunctionFmt",
    )
    require_failure(
        run_fixture(omit_protocol="wl_data_offer_listener"),
        "required Wine listener missing from protocol headers",
    )
    print("wayland listener auditor regressions: ok")


if __name__ == "__main__":
    main()
