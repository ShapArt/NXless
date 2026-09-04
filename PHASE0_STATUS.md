# NXless Phase 0 status

**Verified local source baseline:** `0894ae0d205efd892dbd29c1dcd00e599601a2ce`  
**Remote branch:** `feat/phase0-bsd-mitm`  
**Hardware gate:** NOT COMPLETE

The remote branch contains the Phase 0 portable core, Atmosphere sysmodule source, pinned build/CI configuration, canonical/offline C++ tests, fault-injection tests, recovery/package tooling, the test-only HBMenu probe, and the machine-readable hardware evidence recorder.

The first source publication was imported through GitHub's Git Data API because the development shell could not use ordinary Git transport. Subsequent fixes and tooling changes are published as small reviewable commits on the feature branch.

## Verified

- GitHub Actions Portable Phase 0 gates: PASS;
- GitHub Actions canonical Catch2 host suite: PASS;
- bounded/thread-safe socket registry;
- transparent BSD forwarding contract;
- fail-open boot/recovery policy;
- read-only `nxl:ctl` control plane;
- synchronized atomic control runtime status;
- typed lifecycle hooks for `Socket`, `SocketExempt`, `Accept`, `Close`;
- raw-forward fallback for untyped MITM commands;
- SD recovery/config reads through result-returning low-level FS path;
- fault-injection suite and test-only HBMenu probe;
- machine-readable hardware evidence workflow.

## Hard gates before Phase 1A

1. Issue #2: exact devkitA64 r30 / libnx 4.12.0-1 Switch build.
2. Issue #3: original-Switch hardware acceptance matrix.

Both gates must close with evidence before SOCKS5 TCP implementation starts.

## Merge blockers for PR #1

- exact Switch cross-build evidence is missing;
- original-Switch recovery/network/lifecycle evidence is missing;
- independent review must have zero unresolved Critical/Important findings;
- the draft branch currently carries an SPDX GPL-2.0-only notice; the verbatim GPL-2.0 license text must be restored before merge.
