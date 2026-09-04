#!/usr/bin/env bash
set -euo pipefail
root="${1:-${NXLESS_ATMOSPHERE_ROOT:-}}"
[[ -n "$root" ]] || { echo "Atmosphere source path is required (arg1 or NXLESS_ATMOSPHERE_ROOT)" >&2; exit 2; }
[[ -d "$root/.git" ]] || { echo "not an Atmosphere git checkout: $root" >&2; exit 3; }
head="$(git -C "$root" rev-parse HEAD)"
case "$head" in
  5388824*) ;;
  *) echo "expected Atmosphere 1.11.2 commit 5388824, got $head" >&2; exit 4 ;;
esac
[[ -f "$root/libraries/config/templates/stratosphere.mk" ]] || { echo "missing pinned stratosphere.mk" >&2; exit 5; }
echo "Atmosphere source: PASS ($head)"
