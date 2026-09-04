# NXless

NXless is an open-source Phase 0 proof of concept for a transparent `bsd:u` MITM on Nintendo Switch under Atmosphère.

## Current Phase 0 scope

- HOS 22.5.0 / Atmosphère 1.11.2 (`5388824`)
- devkitA64 r30 / libnx 4.12.0-1 build target
- transparent BSD socket forwarding only
- typed lifecycle hooks for `Socket`, `SocketExempt`, `Accept`, and `Close`
- raw-forward fallback for untyped MITM commands
- read-only `nxl:ctl`
- fail-open boot and `disable.flag` recovery
- bounded diagnostics/socket tracking
- host CI + machine-readable hardware evidence tooling

Phase 1 networking features such as SOCKS5, VLESS, TLS/REALITY/Vision and DNS tunneling are intentionally **not implemented yet**. They remain blocked until the exact Switch cross-build and original-hardware acceptance gates are complete.

See:
- `PHASE0_STATUS.md`
- `docs/architecture.md`
- `docs/security-model.md`
- `docs/compatibility.md`
- `docs/phase-0-acceptance.md`
- GitHub issues #2 and #3

## Safety / recovery

If NXless prevents normal boot or networking during hardware testing, power the console off and create:

`/config/nxless/disable.flag`

The sysmodule must then remain control-only and must not install the BSD MITM.

Removing only `/atmosphere/contents/0100000000004E58` while powered off is the package-level recovery path.

## License

NXless is intended to be distributed under GPL-2.0-only. The draft Phase 0 branch currently carries an SPDX notice; the verbatim GPL-2.0 license text is a merge blocker for PR #1 and must be restored before merge.
