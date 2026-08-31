#!/usr/bin/env python3
"""Regression for the bounded production DXT-surface witness reader."""

from __future__ import annotations

import importlib.util
import pathlib


HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "box86_dxt_stats", HERE / "box86_dxt_stats.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def record(flags, fallback=5):
    return (
        module.WITNESS_MAGIC,
        1,
        6,
        (~module.WITNESS_MAGIC) & 0xFFFFFFFF,
        flags,
        fallback,
    )


base = module.WITNESS_STRONG_SELFTEST | module.WITNESS_ARMED
assert module.witness_verdict(None).startswith("UNAVAILABLE:")
assert module.witness_verdict(record(base)).startswith("NOT_REACHED:")
assert module.witness_verdict(record(
    base | module.WITNESS_INTERCEPTED | module.WITNESS_NATIVE_SEEN
)).startswith("NATIVE_CONFIRMED:")
assert module.witness_verdict(record(
    base | module.WITNESS_INTERCEPTED | module.WITNESS_GUEST_SEEN, 0
)).startswith("FALLBACK_ONLY:")
assert module.witness_verdict(record(
    base | module.WITNESS_INTERCEPTED | module.WITNESS_NATIVE_SEEN
    | module.WITNESS_GUEST_SEEN, 0
)).startswith("MIXED:")
assert module.witness_verdict(record(
    base | module.WITNESS_INTERCEPTED | module.WITNESS_GUEST_FAILED
)).startswith("REFUSED:")
assert module.witness_verdict((0, 1, 6, 0, 0, 5)).startswith("REFUSED:")

print("DXT-surface witness reader regression: ok")
