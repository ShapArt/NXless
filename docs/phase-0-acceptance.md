# Phase 0 Acceptance Criteria

**Phase 0 is not “complete” because it builds.** Every required item below needs fresh evidence attached to the release/PR test record.

## A. Build/reproducibility

- [ ] build uses pinned HOS research target / Atmosphère 1.11.2 **`5388824`** / libnx 4.12.0 **`7644c9b26099aa2d2145bc72a21ee24190e92085`** / devkitA64 r30 toolchain lock;
- [ ] clean container build succeeds from a fresh checkout;
- [ ] build records exact dependency SHAs/versions;
- [ ] release-like package contains no production credentials/secret fixtures;
- [ ] host tests run independently of Switch hardware.

## B. Safe boot/recovery

- [ ] console cold-boots reliably with sysmodule installed;
- [ ] `sdmc:/config/nxless/disable.flag` prevents BSD interception from activating;
- [ ] corrupt config boots in disconnected/fail-open safe mode;
- [ ] missing config boots safely;
- [ ] SD read error path does not fatal-abort;
- [ ] unsupported HOS path leaves MITM disabled and exposes a typed status;
- [ ] uninstall procedure restores normal boot/networking.

## C. BSD MITM correctness

- [ ] `bsd:u` MITM session can be installed/acknowledged on the pinned stack;
- [ ] full pinned command adapter is present and transparent-forward by default;
- [ ] `Socket` fd is associated with a unique client/generation key;
- [ ] `Connect`, `Bind`, `Listen`, `Accept` pass through correctly in no-proxy mode;
- [ ] send/recv/read/write pass through correctly;
- [ ] sendto/recvfrom pass through correctly;
- [ ] Poll/Select passthrough matches baseline test app behavior;
- [ ] Fcntl/Ioctl/GetSockOpt/SetSockOpt required by test apps pass through;
- [ ] Shutdown/Close remove state exactly once;
- [ ] session teardown removes all owned state;
- [ ] fd reuse creates a new generation and cannot access stale state;
- [ ] one selected socket can be marked `ProxyCandidate` in state without changing its traffic yet.

## D. Host tests

Required test classes:

- [ ] socket registry create/close/reuse;
- [ ] two clients using same integer fd never collide;
- [ ] concurrent registry operations under deterministic stress;
- [ ] session teardown while sockets exist;
- [ ] transparent result/errno propagation in fake BSD adapter;
- [ ] malformed config falls back safely;
- [ ] config size/profile limits;
- [ ] secret redaction;
- [ ] IPC version mismatch and oversized payload rejection;
- [ ] recursion architecture test proves direct/original operations do not enter route pipeline;
- [ ] logger ring remains bounded under flood.

## E. Hardware smoke tests

At minimum on original Switch hardware with HOS 22.5.0 + Atmosphère 1.11.2:

- [ ] HBMenu TCP client works before/after NXless installation;
- [ ] TCP echo test with concurrent connections;
- [ ] UDP echo passthrough test;
- [ ] at least two real applications/games that use networking launch and retain baseline network behavior;
- [ ] HOME -> resume does not crash;
- [ ] repeated sleep/wake does not crash;
- [ ] Wi-Fi off/on does not crash;
- [ ] AP reconnect/change does not crash;
- [ ] dock Ethernet path tested if hardware is available;
- [ ] socket churn test does not show registry leak;
- [ ] repeated application launch/close does not increase active-state count;
- [ ] cold boot repeated enough to detect intermittent session-order problems; test count recorded, not described as “many”.

## F. Resource evidence

- [ ] idle sysmodule heap/RSS-equivalent measurement recorded;
- [ ] peak during socket churn recorded;
- [ ] registry high-water mark recorded;
- [ ] no unbounded log/config/socket container growth;
- [ ] target private heap <= 6 MiB, or architecture review documents why it changed;
- [ ] any request to exceed 8 MiB blocks Phase 0 exit pending architecture review.

## G. Stability/failure behavior

- [ ] Wi-Fi unavailable at boot does not abort;
- [ ] network disappears during active socket test without sysmodule crash;
- [ ] allocation-failure injection in portable paths returns typed errors where recoverable;
- [ ] malformed IPC/config cannot trigger intentional fatal assertion;
- [ ] no fd/state leaks detected by host accounting and hardware high-water counters.

## H. Documentation/review gate

- [ ] `docs/compatibility.md` contains the exact tested combination and evidence result;
- [ ] `docs/bsd-mitm-research.md` updated with any observed HOS deviations/workarounds;
- [ ] any workaround has root-cause evidence, not “reference project does this” as justification;
- [ ] security review checks fatal assertions, logging and recovery path;
- [ ] independent code review has no unresolved Critical/Important findings;
- [ ] verification commands and hardware results are included before the words “Phase 0 complete” are used.

## Explicit non-criteria

Phase 0 does **not** require:

- SOCKS5;
- VLESS;
- TLS/REALITY;
- UDP proxying;
- DNS tunneling;
- GUI polish;
- overlay;
- `bsd:s`/`bsd:a` interception.

Adding those before this checklist passes is scope creep and increases boot risk without proving the foundation.
