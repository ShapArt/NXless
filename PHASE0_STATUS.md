# NXless Phase 0 status

**Verified local source baseline:** `0894ae0d205efd892dbd29c1dcd00e599601a2ce`  
**Remote branch:** `feat/phase0-bsd-mitm`  
**Hardware gate:** NOT COMPLETE

The remote branch now contains the Phase 0 portable core, sysmodule source, pinned build/CI configuration, canonical/offline C++ tests, fault-injection tests, recovery/package tooling, and the test-only HBMenu probe source. The source bootstrap was imported through GitHub's Git Data API because the development shell cannot resolve `github.com` for ordinary `git push`.

The granular 21-commit local Conventional/DCO history is still preserved in the verified local repository/bundle, but this first remote source publication is a snapshot commit rather than a byte-for-byte replay of those local commit SHAs.

## Verified locally before publication

- 49 C++ tests under ASan/UBSan: PASS;
- strict production compile with exceptions/RTTI disabled and warnings-as-errors: PASS;
- package policy 9/9: PASS;
- dependency locks and pinned CI/container artifacts: PASS;
- Title ID local collision gate for `0100000000004E58`: PASS;
- bounded/thread-safe socket registry;
- transparent BSD forwarding contract;
- fail-open boot/recovery policy;
- read-only `nxl:ctl` control plane;
- typed lifecycle hooks for `Socket`, `SocketExempt`, `Accept`, `Close`;
- raw-forward fallback for untyped MITM commands;
- SD recovery/config reads through result-returning low-level FS path;
- fault-injection suite and test-only HBMenu probe source.

## Publication note

The large machine-readable hardware evidence recorder from the local baseline is being imported separately from the core source bootstrap. Until that import is complete, the remote branch must not be treated as the sole archival copy of the local Phase 0 tooling snapshot.

## Environment blockers

1. The original development shell cannot complete canonical Catch2 FetchContent because its DNS cannot resolve `github.com`; GitHub Actions is intended to provide this networked canonical host gate.
2. A real devkitA64 r30 / libnx 4.12.0-1 cross-build has not yet been produced in the current runner.
3. Original-Switch boot/lifecycle testing has not yet been run.

## Required before Phase 1

Phase 1A (SOCKS5 TCP) must not start until:

- an exact devkitA64 r30 / libnx 4.12.0-1 build succeeds;
- the Phase 0 package boots repeatedly on original Switch hardware;
- `disable.flag` recovery is proven;
- TCP/UDP transparent-baseline tests pass;
- at least two real networked applications preserve baseline behavior;
- sleep/wake, Wi-Fi reconnect/AP change, app churn and resource counters pass the recorded acceptance matrix.
