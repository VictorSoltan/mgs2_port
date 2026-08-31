#!/bin/sh
# FINALPLAY23 fixed production route: FINALPLAY22 plus the two-byte movie guard
# that closes the NULL DirectShow graph dereference measured on 2026-08-31.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=finalplay23
exec "$HERE/launch-play-dxvk-fp17.sh"
