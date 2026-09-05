# NXless Phase 0 status

**Remote Phase 0 branch:** `feat/phase0-bsd-mitm`  
**Remote implementation line:** published and CI-verified  
**Hardware gate:** NOT COMPLETE

The GitHub branch contains the Phase 0 portable core, Atmosphere sysmodule source, pinned build/CI configuration, canonical and offline C++ tests, fault-injection tests, package/recovery tooling, machine-readable hardware evidence recorder, the test-only HBMenu probe source, and the hardware-test operator runbook.

The initial source publication was imported through GitHub's Git Data API because the original development shell could not resolve `github.com` for ordinary Git transport. Follow-up fixes and tooling changes are now published as small reviewable commits on the feature branch.

## Verified

- GitHub Actions Portable Phase 0 gates: PASS;
- GitHub Actions canonical Catch2 host suite: PASS;
- offline ASan/UBSan suite: PASS;
- strict production compile with exceptions/RTTI disabled and warnings-as-errors: PASS;
- package policy: PASS;
- dependency / CI / container pins: PASS;
- Title ID collision guard for `0100000000004E58`: PASS;
- machine-readable hardware recorder and tooling tests are present in the remote tree;
- read-only `nxl:ctl`, fail-open boot/recovery policy and bounded socket state are covered by host/source-contract tests;
- GPL-2.0-only license text is present as a complete verbatim license document;
- `docs/hardware-testing.md` documents the machine-readable hardware acceptance workflow.

## Review findings already fixed

- control service publication now happens only after its thread resources are ready;
- `nxl:ctl` runtime status uses one atomic packed snapshot for `(RuntimeMode, last_internal_error)`, removing a cross-thread data race and torn-state window;
- SD recovery/config reads avoid aborting libstratosphere mount initialization and use result-returning libnx FS calls;
- exhausted MITM client-context IDs fall back to Atmosphere raw-forward instead of creating an untracked context 0 session;
- preflight evidence reports distinguish host-only preflight success from a full Phase 0 hardware PASS;
- the repository license was repaired after a malformed import and the missing GPL sections are present again.

## Hard gates before Phase 1A

- GitHub issue #2: produce an exact devkitA64 r30 / libnx 4.12.0-1 Switch build.
- GitHub issue #3: pass the original-Switch hardware acceptance matrix.

Both issues must be closed with evidence before SOCKS5 TCP implementation starts.

## Required before merge / Phase 1

- exact devkitA64 r30 / libnx 4.12.0-1 cross-build succeeds;
- Phase 0 package boots repeatedly on original Switch hardware;
- `disable.flag` recovery is proven;
- TCP/UDP transparent-baseline tests pass;
- at least two different real networked applications preserve baseline behavior;
- sleep/wake, Wi-Fi reconnect/AP change, app churn and resource counters pass the recorded matrix;
- independent review has no unresolved Critical or Important findings.
