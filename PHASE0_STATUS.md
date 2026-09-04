# NXless Phase 0 status

**Remote Phase 0 branch:** `feat/phase0-bsd-mitm`  
**Remote implementation line:** published and CI-verified  
**Hardware gate:** NOT COMPLETE

The GitHub branch now contains the Phase 0 portable core, Atmosphere sysmodule source, pinned build/CI configuration, canonical and offline C++ tests, fault-injection tests, package/recovery tooling, machine-readable hardware evidence recorder, and the test-only HBMenu probe source.

The initial source publication was imported through GitHub's Git Data API because the original development shell could not resolve `github.com` for ordinary Git transport. Follow-up fixes are committed directly on the feature branch and validated by GitHub Actions.

## Verified

- GitHub Actions Portable Phase 0 gates: PASS;
- GitHub Actions canonical Catch2 host suite: PASS;
- offline ASan/UBSan suite: PASS;
- strict production compile with exceptions/RTTI disabled and warnings-as-errors: PASS;
- package policy: PASS;
- dependency / CI / container pins: PASS;
- Title ID collision guard for `0100000000004E58`: PASS;
- machine-readable hardware recorder and tooling tests are present in the remote tree;
- read-only `nxl:ctl`, fail-open boot/recovery policy and bounded socket state are covered by host/source-contract tests.

## Review findings already fixed

- control service publication now happens only after its thread resources are ready;
- `nxl:ctl` runtime status uses one atomic packed snapshot for `(RuntimeMode, last_internal_error)`, removing a cross-thread data race and torn-state window;
- SD recovery/config reads avoid aborting libstratosphere mount initialization and use result-returning libnx FS calls;
- exhausted MITM client-context IDs fall back to Atmosphere raw-forward instead of creating an untracked context 0 session.

## Hard gates before Phase 1A

- GitHub issue #2: produce an exact devkitA64 r30 / libnx 4.12.0-1 Switch build.
- GitHub issue #3: pass the original-Switch hardware acceptance matrix.

Both issues must be closed with evidence before SOCKS5 TCP implementation starts.

## License provenance note

The remote repository contains the complete GPL-2.0 license text. A historical locally archived LICENSE copy has a different Git blob hash due to text-format/version provenance, so remote documentation must not claim byte-for-byte identity with that archived blob. The project licensing intent remains GPL-2.0-only.

## Required before merge / Phase 1

- exact devkitA64 r30 / libnx 4.12.0-1 cross-build succeeds;
- Phase 0 package boots repeatedly on original Switch hardware;
- `disable.flag` recovery is proven;
- TCP/UDP transparent-baseline tests pass;
- at least two different real networked applications preserve baseline behavior;
- sleep/wake, Wi-Fi reconnect/AP change, app churn and resource counters pass the recorded matrix;
- independent review has no unresolved Critical or Important findings.
