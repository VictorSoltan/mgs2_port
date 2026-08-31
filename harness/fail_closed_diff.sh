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

mgs2_nonempty_equal()
{
    [ -n "$1" ] && [ -n "$2" ] && [ "$1" = "$2" ]
}

# Generate a stable traditional patch body for every regular-file difference
# between two trees.  GNU diff -N covers files added under whole new
# directories, which the old `diff -rq | grep " differ"` refresh missed.
# Empty one-sided files and non-text differences cannot be represented by this
# patch format, so refuse them instead of producing an incomplete record.
mgs2_patch_tree()
{
    mgs2_patch_out=$1
    mgs2_patch_err=$2
    mgs2_patch_old=$3
    mgs2_patch_new=$4
    mgs2_patch_raw="${mgs2_patch_out}.raw.$$"
    mgs2_patch_old_list="${mgs2_patch_out}.old.$$"
    mgs2_patch_new_list="${mgs2_patch_out}.new.$$"

    if ! (cd "$mgs2_patch_old" && find . -type f ! -name '*.orig' -print \
            | sed 's|^\./||' | sort) >"$mgs2_patch_old_list" \
            || ! (cd "$mgs2_patch_new" && find . -type f ! -name '*.orig' -print \
            | sed 's|^\./||' | sort) >"$mgs2_patch_new_list"; then
        echo "could not enumerate patch input trees" >"$mgs2_patch_err"
        rm -f "$mgs2_patch_raw" "$mgs2_patch_old_list" "$mgs2_patch_new_list"
        return 2
    fi

    if ! {
        comm -23 "$mgs2_patch_old_list" "$mgs2_patch_new_list" \
            | while IFS= read -r mgs2_patch_rel; do
                [ -s "$mgs2_patch_old/$mgs2_patch_rel" ] || {
                    echo "cannot record deleted empty file: $mgs2_patch_rel" >&2
                    exit 1
                }
            done \
        && comm -13 "$mgs2_patch_old_list" "$mgs2_patch_new_list" \
            | while IFS= read -r mgs2_patch_rel; do
                [ -s "$mgs2_patch_new/$mgs2_patch_rel" ] || {
                    echo "cannot record added empty file: $mgs2_patch_rel" >&2
                    exit 1
                }
            done
    } 2>"$mgs2_patch_err"; then
        rm -f "$mgs2_patch_raw" "$mgs2_patch_old_list" "$mgs2_patch_new_list"
        return 2
    fi

    if diff -ruN -x '*.orig' "$mgs2_patch_old" "$mgs2_patch_new" \
            >"$mgs2_patch_raw" 2>"$mgs2_patch_err"; then
        mgs2_patch_rc=0
    else
        mgs2_patch_rc=$?
    fi
    if [ "$mgs2_patch_rc" -gt 1 ] \
            || grep -Eq '^(Binary files |Only in |File |Symbolic links )' \
                "$mgs2_patch_raw"; then
        [ "$mgs2_patch_rc" -gt 1 ] \
            || echo "tree contains a difference traditional patch cannot record" \
                >>"$mgs2_patch_err"
        rm -f "$mgs2_patch_raw" "$mgs2_patch_old_list" "$mgs2_patch_new_list"
        return 2
    fi

    awk -v old="$mgs2_patch_old/" -v new="$mgs2_patch_new/" '
        index($0, "diff -ruN ") == 1 {next}
        index($0, "--- " old) == 1 {
            rel = substr($0, 5 + length(old)); sub(/\t.*/, "", rel)
            print "--- a/" rel; next
        }
        index($0, "+++ " new) == 1 {
            rel = substr($0, 5 + length(new)); sub(/\t.*/, "", rel)
            print "+++ b/" rel; next
        }
        {print}
    ' "$mgs2_patch_raw" >"$mgs2_patch_out" || {
        echo "could not normalise patch paths" >>"$mgs2_patch_err"
        rm -f "$mgs2_patch_raw" "$mgs2_patch_old_list" "$mgs2_patch_new_list"
        return 2
    }
    rm -f "$mgs2_patch_raw" "$mgs2_patch_old_list" "$mgs2_patch_new_list"
    return 0
}
