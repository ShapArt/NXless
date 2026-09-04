# NXless

NXless is an experimental open-source system-wide TCP/UDP proxy/tunnel project for compatible Nintendo Switch Horizon applications under Atmosphere.

Phase 0 is intentionally narrow: a safe `bsd:u` interception proof of concept with transparent forwarding and bounded socket-state accounting. **No SOCKS5, VLESS, TLS, DNS interception, or packet-level VPN is implemented yet.**

## Current target

- Nintendo Switch (original hardware)
- HOS 22.5.0
- Atmosphere 1.11.2 (`5388824`)
- devkitA64 r30
- libnx 4.12.0-1 build baseline
- Program ID: `0100000000004E58`

## Phase 0 design

NXless exposes a read-only `nxl:ctl` status service first, then enables the `bsd:u` MITM only after the HOS compatibility, SD recovery/config, and control-service gates pass.

Only the fd-lifecycle hooks required for state accounting are typed (`Socket`, `SocketExempt`, `Accept`, `Close`). Other BSD commands rely on Atmosphere's MITM raw-forward path to the original service, reducing compatibility risk with newer command surfaces.

Safe recovery is part of the design: `/config/nxless/disable.flag` prevents BSD interception. Ordinary config/SD errors are intended to fail open rather than turn into a boot-time networking failure.

## Verification status

The portable Phase 0 implementation currently passes its available offline gates:

- 49 C++ tests under ASan/UBSan offline harness
- strict production compile with `-fno-exceptions -fno-rtti -Werror`
- package-policy self-tests
- dependency/title-ID/source-contract gates
- pinned host CI/container supply-chain checks

The hardware gate is **not complete**. A real devkitA64 r30 cross-build and tests on an original Switch running HOS 22.5.0 / Atmosphere 1.11.2 are still required before Phase 1 (SOCKS5 TCP) begins.

See the Phase 0 design and acceptance documents in `docs/` on this branch.
