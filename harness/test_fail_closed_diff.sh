#!/bin/sh
# Regression for the exact fail-open boundary used by verify_rebuild.sh.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck disable=SC1091
. "$REPO/harness/fail_closed_diff.sh"

WORK=$(mktemp -d /tmp/mgs2-diff-regression.XXXXXX)
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT HUP INT TERM

mkdir -p "$WORK/reconstructed" "$WORK/live"
: > "$WORK/reconstructed/same.c"
: > "$WORK/live/same.c"

if ! mgs2_diff_tree "$WORK/equal.out" "$WORK/equal.err" \
        "$WORK/reconstructed" "$WORK/live"; then
    echo "FAIL: equal trees did not return 0" >&2
    exit 1
fi

: > "$WORK/live/unrecorded.c"
if mgs2_diff_tree "$WORK/different.out" "$WORK/different.err" \
        "$WORK/reconstructed" "$WORK/live"; then
    echo "FAIL: an unrecorded live .c file returned 0" >&2
    exit 1
else
    rc=$?
fi
[ "$rc" = 1 ] || {
    echo "FAIL: a real difference returned $rc instead of 1" >&2
    exit 1
}
grep -q 'unrecorded.c' "$WORK/different.out" || {
    echo "FAIL: the extra live source was absent from diff output" >&2
    exit 1
}

if mgs2_diff_tree "$WORK/error.out" "$WORK/error.err" \
        "$WORK/reconstructed" "$WORK/definitely-missing"; then
    echo "FAIL: a missing comparison tree returned 0" >&2
    exit 1
else
    rc=$?
fi
[ "$rc" -gt 1 ] || {
    echo "FAIL: a missing tree returned $rc instead of a diff error" >&2
    exit 1
}
[ -s "$WORK/error.err" ] || {
    echo "FAIL: diff error diagnostics were not captured" >&2
    exit 1
}

echo "ok     equal tree => 0"
echo "ok     extra live .c => 1 and named"
echo "ok     missing tree => $rc and diagnostic"
