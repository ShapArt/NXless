# Building NXless Phase 0

Phase 0 is a transparent `bsd:u` MITM proof of concept. It contains no SOCKS5, VLESS, TLS, DNS interception, NRO application, or overlay.

## Pinned build baseline

- Nintendo Switch HOS: 22.5.0 for the Phase 0 compatibility gate.
- Atmosphere: 1.11.2, exact source commit `5388824`.
- libnx: 4.12.0, commit `7644c9b26099aa2d2145bc72a21ee24190e92085`.
- devkitA64: r30 / GCC 16.1.0.

The devkitA64 r30 package set is verified together with `libnx 4.12.0-1`; r30 alone is not treated as proof of the libnx version.

The build deliberately rejects a different Atmosphere checkout or Switch compiler instead of silently accepting ABI drift.

## One-command verified Phase 0 build

On a normal Linux build host with the pinned devkitPro packages installed and GitHub reachable, the preferred entry point is:

```sh
export DEVKITPRO=/opt/devkitpro
make phase0-build
```

The command refuses a dirty tree, verifies the dependency locks, runs the hardware/tooling source contracts, creates a commit-bound machine-readable evidence record, runs the canonical host suite, verifies devkitA64 r30 + libnx 4.12.0-1, performs a clean Switch package build, and records the resulting `output/NXless-phase0.zip` SHA-256.

If `third_party/Atmosphere` does not exist, the orchestrator fetches the official Atmosphere tag `1.11.2` from GitHub and then requires `verify-atmosphere-source.sh` to resolve it to commit `5388824…`. Generated evidence and the fetched checkout are ignored by git, so creating them cannot make the source tree dirty. Set `NO_FETCH_ATMOSPHERE=1` to require an existing checkout, or pass `NXLESS_ATMOSPHERE_ROOT=/path/to/Atmosphere`.

An existing evidence record is never overwritten. Use `RECORD=/path/to/new-record.json` to choose a different path.

## Source checkout

Place the exact Atmosphere checkout at `third_party/Atmosphere`, or set `NXLESS_ATMOSPHERE_ROOT` to another checkout. Before compiling, NXless runs `scripts/verify-atmosphere-source.sh` and `scripts/verify-switch-toolchain.sh`.

Example:

```sh
git clone https://github.com/Atmosphere-NX/Atmosphere third_party/Atmosphere
git -C third_party/Atmosphere checkout 5388824
export DEVKITPRO=/opt/devkitpro
make switch
```

The current ChatGPT build runner does not contain devkitPro/libstratosphere, so Horizon cross-compilation is not claimed as verified here. Host tests and source-level checks are separate evidence and do not replace a real Switch build.

## Package

After a successful Switch build:

```sh
make -C sysmodule dist NXLESS_ATMOSPHERE_ROOT="$PWD/third_party/Atmosphere"
```

`dist` creates and verifies only these Phase 0 files:

- `atmosphere/contents/0100000000004E58/exefs.nsp`
- `atmosphere/contents/0100000000004E58/flags/boot2.flag`
- `config/nxless/example.toml`

The verifier rejects NRO/OVL files, private-key markers, VLESS URIs, subscription URLs, and files outside NXless-owned Phase 0 paths.

## NPDM capability note

The service ACL is intentionally narrow: NXless hosts only `nxl:ctl` and the `bsd:u` MITM port, and accesses only `fsp-srv` and `bsd:u`. The filesystem permission mask is restricted to `0x0000000000200000` (FsAccessFlag bit 21, `SdCard`). For HOS 21.0.0+ the documented `CanMountSdCard` permission mask includes this bit; debug/full-permission bits are not requested. Hardware validation on HOS 22.5.0 remains part of the Phase 0 gate.

Boot-time recovery/config reads use libnx `fsInitialize()` and `fsOpenSdCardFileSystem()` directly instead of libstratosphere's aborting system-FS initialization/mount path. A failure to obtain `fsp-srv`, open the SD filesystem, probe `disable.flag`, or read the config must therefore leave BSD MITM disabled rather than fatal-aborting the console.
