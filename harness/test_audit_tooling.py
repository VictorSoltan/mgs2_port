#!/usr/bin/env python3
"""Small regressions for the non-gameplay audit-tooling fixes."""

from __future__ import annotations

import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    present = load("audit_dxvk_present", "dxvk_present_count.py")
    original = present.exported_rva
    present.exported_rva = lambda unused: (_ for _ in ()).throw(
        RuntimeError("missing test export"))
    try:
        try:
            present.resolve_rva("test-d3d9.dll")
        except RuntimeError as error:
            assert "independently verified --rva" in str(error)
        else:
            raise AssertionError("export failure did not fail closed")
        assert present.resolve_rva("test-d3d9.dll", 0x1234) == (0x1234, "argument")
    finally:
        present.exported_rva = original

    island = load("audit_island_ab", "island_ab_read.py")
    assert island.exact_sign_p(10, 0) == island.exact_sign_p(0, 10)
    assert island.exact_sign_p(0, 10) < 0.01
    malformed = [{
        "cycle": 7,
        "routed": 10.0,
        "routed_n": 0,
        "routed_calls": 1,
        "unrouted": 11.0,
        "unrouted_n": 1,
        "unrouted_calls": 1,
    }]
    try:
        island.work_normalised(malformed, iterations=10)
    except ValueError as error:
        assert "zero per-arm frame count" in str(error)
    else:
        raise AssertionError("zero frame denominator was accepted")

    env = load("audit_repo_env", "repo_env.py")
    assert env._parse_value("/tmp/tree#candidate") == "/tmp/tree#candidate"
    assert env._parse_value('"/tmp/two  spaces/#candidate" # note') \
        == "/tmp/two  spaces/#candidate"
    assert env._parse_value(r"/tmp/two\ \ spaces#candidate") \
        == "/tmp/two  spaces#candidate"
    try:
        env._parse_value("/tmp/unquoted  whitespace")
    except ValueError:
        pass
    else:
        raise AssertionError("ambiguous unquoted whitespace was silently collapsed")

    print("audit tooling Python regressions: ok")


if __name__ == "__main__":
    main()
