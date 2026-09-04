# NXless

NXless is an open-source Nintendo Switch network tunneling project for Atmosphere.

The current development milestone is **Phase 0**: a safety-first transparent `bsd:u` MITM proof of concept for HOS 22.5.0 / Atmosphere 1.11.2. Phase 0 does **not** implement SOCKS5, VLESS, TLS, REALITY, Vision, DNS tunneling, or a user-facing VPN client yet.

## Current Phase 0 scope

- transparent forwarding through Atmosphere's `bsd:u` MITM;
- typed hooks only where NXless needs socket lifecycle state;
- read-only `nxl:ctl` status/diagnostics service;
- fail-open boot policy and `disable.flag` recovery;
- bounded socket registry, log ring, config parser and diagnostics;
- pinned host CI / dependency locks;
- machine-readable hardware evidence recorder;
- test-only HBMenu network probe source;
- original-Switch hardware gate before proxy functionality begins.

## Supported research target

- Nintendo Switch / Horizon OS 22.5.0
- Atmosphere 1.11.2 (`5388824`)
- devkitA64 r30
- libnx package 4.12.0-1

Other HOS versions currently keep BSD interception disabled rather than guessing compatibility.

## Project status

Host verification is green in GitHub Actions, including the canonical Catch2 suite. Phase 0 is **not complete** until the exact Switch cross-build and original-hardware acceptance matrix pass.

Track the hard gates in GitHub issues **#2** (exact Switch build) and **#3** (hardware acceptance).

See `PHASE0_STATUS.md`, `docs/architecture.md`, `docs/security-model.md`, and `docs/phase-0-acceptance.md` for details.

## License

NXless is licensed under **GPL-2.0-only**. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.
