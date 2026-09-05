#!/usr/bin/env bash
set -euo pipefail
: "${DEVKITPRO:?DEVKITPRO must be set}"
compiler="$DEVKITPRO/devkitA64/bin/aarch64-none-elf-gcc"
[[ -x "$compiler" ]] || { echo "missing $compiler" >&2; exit 2; }
version="$($compiler -dumpfullversion -dumpversion)"
[[ "$version" == 16.1.0* ]] || { echo "expected GCC 16.1.0 (devkitA64 r30), got $version" >&2; exit 3; }

pkg_query=""
if command -v dkp-pacman >/dev/null 2>&1; then
  pkg_query="dkp-pacman"
elif command -v pacman >/dev/null 2>&1; then
  pkg_query="pacman"
else
  echo "pacman package query tool is required to prove exact devkitA64/libnx package versions" >&2
  exit 4
fi

devkit_pkg="$($pkg_query -Q devkitA64 2>/dev/null || true)"
[[ "$devkit_pkg" == "devkitA64 r30-1" || "$devkit_pkg" == "devkitA64 r30" ]] || {
  echo "expected devkitA64 r30, got: ${devkit_pkg:-not installed}" >&2; exit 5;
}
libnx_pkg="$($pkg_query -Q libnx 2>/dev/null || true)"
[[ "$libnx_pkg" == "libnx 4.12.0-1" ]] || {
  echo "expected libnx 4.12.0-1 (v4.12.0 commit 7644c9b26099aa2d2145bc72a21ee24190e92085), got: ${libnx_pkg:-not installed}" >&2; exit 6;
}

printf 'switch toolchain: devkit_pkg="%s"; gcc="%s"; libnx_pkg="%s"\n' \
  "$devkit_pkg" "$version" "$libnx_pkg"
