#!/bin/sh
# Source-only helper: preserve diff(1)'s three-state result while capturing its
# output.  A provenance check must distinguish "equal" (0), "different" (1)
# and "comparison failed" (>1); piping diff into wc loses that distinction.

mgs2_diff_tree()
{
    mgs2_diff_out=$1
    mgs2_diff_err=$2
    shift 2

    if diff -rq "$@" >"$mgs2_diff_out" 2>"$mgs2_diff_err"; then
        return 0
    else
        mgs2_diff_rc=$?
        return "$mgs2_diff_rc"
    fi
}
