#!/usr/bin/env python3
"""Reviewed phase cuts inside ``context_apply_draw_state()``.

The line spans are the contiguous guest control-flow transactions.  ``roots``
are the native callees reachable from each span; B adds the GL state-table
callbacks and D adds the selected GLSL shader backend callback.  Keeping this
description in one module makes the ABI admission gate and offline perf
attribution use the same boundary.
"""

import pathlib
import re

import island_icall_audit


CONTEXT_GL = "context_gl.c"
PHASE_MARKERS = {
    "B": ("MGS2_PHASE_B_BEGIN", "MGS2_PHASE_B_END"),
    "C": ("MGS2_PHASE_C_BEGIN", "MGS2_PHASE_C_END"),
    "D": ("MGS2_PHASE_D_BEGIN", "MGS2_PHASE_D_END"),
}


def _state_apply_targets(bodies):
    """GL state-table callbacks that may be selected by the phase-B loop."""
    result = set()
    pattern = re.compile(
        r"\{\s*[^{}]+,\s*\{\s*[^{},]+,\s*([A-Za-z_]\w*|NULL|0)\s*,?\s*\}"
        r"\s*,\s*[^{}]+\}")
    for filename in ("ffp_gl.c", "glsl_shader.c"):
        text = (pathlib.Path(island_icall_audit.SRC_DIR) / filename).read_text(errors="replace")
        for match in pattern.finditer(text):
            target = match.group(1)
            if target in bodies:
                result.add(target)
    result.update(name for name in ("multistate_apply_2", "multistate_apply_3") if name in bodies)
    return result


def phase_spec(name, bodies=None):
    name = name.upper()
    if name not in "ABCD":
        raise ValueError("unknown draw-state phase %s" % name)
    bodies = bodies or island_icall_audit.functions_by_file()
    if name == "A":
        # p70b split the marked entry from the transaction it performs, so the
        # contiguous span lives in the body function when that exists.
        entry = ("mgs2_draw_state_phase_a_body" if "mgs2_draw_state_phase_a_body" in bodies
                 else "mgs2_draw_state_phase_a_island")
        _filename, first, lines = bodies[entry]
        last = lines[-1][0]
    else:
        _filename, _start, function_body = bodies["context_apply_draw_state"]
        begin, end = PHASE_MARKERS[name]
        first = next(line_no for line_no, text in function_body if begin in text)
        last = next(line_no for line_no, text in function_body if end in text)
        lines = [(line_no, text) for line_no, text in function_body if first <= line_no <= last]
    syntax = list(island_icall_audit.mask_c_lines([text for _line_no, text in lines]))
    call_re = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
    roots = {match.group(1) for text in syntax for match in call_re.finditer(text)
             if match.group(1) in bodies}
    if name == "A":
        roots.add(entry)
    elif name == "B":
        roots.update(_state_apply_targets(bodies))
    elif name == "D":
        # The production route selected GLSL. Other shader backends are not
        # possible targets in this capture and would make admission needlessly
        # describe code that never runs on the handheld.
        roots.add("shader_glsl_apply_draw_state")
    return {
        "name": name,
        "label": "phase-%s" % name,
        "lines": (first, last),
        "body": lines,
        "roots": sorted(roots),
    }
