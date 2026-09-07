#!/usr/bin/env bash
set -euo pipefail
root="${1:-${NXLESS_ATMOSPHERE_ROOT:-}}"
[[ -n "$root" ]] || { echo "Atmosphere source path is required (arg1 or NXLESS_ATMOSPHERE_ROOT)" >&2; exit 2; }
[[ -d "$root/.git" ]] || { echo "not an Atmosphere git checkout: $root" >&2; exit 3; }
expected="5388824be146a89619e8d641acd64599cf1c5f62"
head="$(git -C "$root" rev-parse HEAD)"
[[ "$head" == "$expected" ]] || {
  echo "expected Atmosphere 1.11.2 commit $expected, got $head" >&2
  exit 4
}
[[ -f "$root/libraries/config/templates/stratosphere.mk" ]] || { echo "missing pinned stratosphere.mk" >&2; exit 5; }
printf 'Atmosphere source: commit="%s"\n' "$head"
