#!/bin/sh
# Regressions for F1--F7 in MGS2_BUG_AUDIT_2026-08-28.md.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck disable=SC1091
. "$REPO/harness/fail_closed_diff.sh"

TMP=$(mktemp -d /tmp/mgs2-audit-tooling.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

OLD="$TMP/old"
NEW="$TMP/new"
REB="$TMP/rebuilt"
mkdir -p "$OLD/kept" "$NEW/kept" "$NEW/added/nested" "$REB"
printf '%s\n' old > "$OLD/kept/modified.txt"
printf '%s\n' new > "$NEW/kept/modified.txt"
printf '%s\n' deleted > "$OLD/deleted.txt"
printf '%s\n' added > "$NEW/added/nested/source.c"

mgs2_patch_tree "$TMP/body.patch" "$TMP/body.err" "$OLD" "$NEW"
grep -Fq -- '--- a/added/nested/source.c' "$TMP/body.patch"
grep -Fq -- '+++ b/added/nested/source.c' "$TMP/body.patch"
cp -R "$OLD/." "$REB/"
(cd "$REB" && patch -p1 -E --silent < "$TMP/body.patch")
if ! mgs2_diff_tree "$TMP/rebuilt.diff" "$TMP/rebuilt.err" "$REB" "$NEW"; then
    echo "generated complete patch did not reconstruct added/deleted files" >&2
    exit 1
fi

mkdir -p "$TMP/empty-old" "$TMP/empty-new"
: > "$TMP/empty-new/unrepresentable-empty-file"
if mgs2_patch_tree "$TMP/empty.patch" "$TMP/empty.err" \
        "$TMP/empty-old" "$TMP/empty-new"; then
    echo "empty added file was silently omitted from complete patch" >&2
    exit 1
fi

mgs2_nonempty_equal abc abc
if mgs2_nonempty_equal '' ''; then
    echo "empty base identities compared equal" >&2
    exit 1
fi

grep -Fq 'FAIL   rebuilt $got, release is $want -- the tree carries' \
    "$REPO/harness/verify_rebuild.sh"
grep -A5 -F 'FAIL   rebuilt $got, release is $want -- the tree carries' \
    "$REPO/harness/verify_rebuild.sh" | grep -Fq 'fail=1'

python3 "$REPO/harness/test_audit_tooling.py"
PYTHONPATH="$REPO/harness" python3 "$REPO/harness/test_wayland_listener_audit.py"
echo "audit tooling shell regressions: ok"
