# NXless Phase 0 status

**Local verified implementation HEAD:** `0894ae0d205efd892dbd29c1dcd00e599601a2ce`  
**Remote branch:** `feat/phase0-bsd-mitm`  
**Hardware gate:** NOT COMPLETE

This branch is currently a documentation/bootstrap view of the Phase 0 work while the full source history remains in the local verified repository snapshot. The shell runner used during development cannot resolve `github.com`, so the complete 21-commit local history cannot be pushed through normal Git transport from that environment yet.

## Verified locally

- bounded/thread-safe socket registry;
- transparent BSD forwarding contract;
- fail-open boot/recovery policy;
- read-only `nxl:ctl` control plane;
- HOS 22.5.0 BSD command/wire research;
- typed lifecycle hooks for `Socket`, `SocketExempt`, `Accept`, `Close`;
- raw-forward fallback for untyped MITM commands;
- SD recovery/config reads through result-returning low-level FS path;
- sysmodule/package layout and recovery verifier;
- fault-injection suite;
- HBMenu Phase 0 probe source;
- machine-readable hardware evidence tooling;
- pinned host CI/container supply-chain configuration.

Most recent available offline verification before this branch bootstrap:

- 49 C++ tests under ASan/UBSan: PASS;
- strict production compile with exceptions/RTTI disabled and warnings-as-errors: PASS;
- package policy 9/9: PASS;
- dependency locks: PASS;
- Title ID local collision gate for `0100000000004E58`: PASS.

## Environment blockers

The development runner currently cannot complete these external gates:

1. canonical Catch2 FetchContent because shell DNS cannot resolve `github.com`;
2. devkitA64 r30 cross-build because the exact devkitPro toolchain is unavailable in the runner;
3. original-Switch boot/lifecycle testing because no console is attached.

## Required before Phase 1

Phase 1A (SOCKS5 TCP) must not start until:

- an exact devkitA64 r30 / libnx 4.12.0 build succeeds;
- the Phase 0 package boots repeatedly on original Switch hardware;
- `disable.flag` recovery is proven;
- TCP/UDP transparent-baseline tests pass;
- at least two real networked applications preserve baseline behavior;
- sleep/wake, Wi-Fi reconnect/AP change, app churn and resource counters pass the recorded acceptance matrix.

## Git bootstrap note

The GitHub branch is intentionally a safe documentation bootstrap, not a claim that the complete source tree has been published. The complete source snapshot and granular local commit history should be pushed through normal Git transport once a runner/machine with GitHub network access is used.
