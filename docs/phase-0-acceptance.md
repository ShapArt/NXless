# NXless Phase 0 acceptance gate

Phase 0 exists to prove that NXless can interpose on `bsd:u` transparently and recoverably before any proxy protocol is introduced.

Phase 1A (SOCKS5 TCP) is **blocked** until every required item below has objective evidence.

## Build and source identity

- [ ] Git working tree used for the build is clean.
- [ ] Source commit is recorded in the evidence JSON.
- [ ] Atmosphere is exactly 1.11.2 / `5388824be146a89619e8d641acd64599cf1c5f62`.
- [ ] devkitA64 is r30.
- [ ] installed libnx package is exactly 4.12.0-1.
- [ ] `scripts/verify-switch-toolchain.sh` passes.
- [ ] pinned Atmosphere source verifier passes.
- [ ] clean `make phase0-build` succeeds.
- [ ] `output/NXless-phase0.zip` passes the package verifier.
- [ ] package SHA-256 is recorded.

This build gate is tracked by GitHub issue #2.

## Host verification

The source revision used for hardware testing must have:

- [x] Portable Phase 0 GitHub Actions gates passing.
- [x] Canonical Catch2 GitHub Actions suite passing.
- [x] Offline ASan/UBSan suite available and passing in CI.
- [x] Strict production compile with `-fno-exceptions -fno-rtti -Werror` passing.
- [x] Dependency lock and Title ID checks passing.

A later source revision must re-run these checks; a green older revision is not transferable evidence.

## Recovery / cold boot

On original Nintendo Switch hardware running HOS 22.5.0 / Atmosphere 1.11.2:

- [ ] `disable.flag` present: 10 successful cold boots.
- [ ] `nxl:ctl` reports `SafeDisabled` while the recovery flag is present.
- [ ] transparent BSD MITM enabled: 20 successful cold boots.
- [ ] `nxl:ctl` reports `DisconnectedPassthrough` after successful Phase 0 admission.
- [ ] removing only `/atmosphere/contents/0100000000004E58` while powered off restores normal boot/network behavior.
- [ ] malformed/unreadable optional config cannot make boot fatal.

## Transparent network baseline

Using the test-only NXlessProbe and a controlled echo endpoint:

- [ ] TCP echo succeeds without NXless.
- [ ] TCP echo succeeds with transparent NXless MITM.
- [ ] UDP echo succeeds without NXless.
- [ ] UDP echo succeeds with transparent NXless MITM.
- [ ] concurrent socket probe stays within configured Phase 0 bounds.
- [ ] no nested/recursive NXless proxy connection exists in Phase 0.

## Real applications

- [ ] at least two different real networked applications/games preserve their baseline network behavior with the transparent MITM installed.

Record application names/title IDs where practical; do not use two launches of the same application as two independent applications.

## Lifecycle matrix

- [ ] HOME/resume repetitions pass.
- [ ] sleep/wake x20 passes.
- [ ] Wi-Fi off/on x10 passes.
- [ ] access-point change x5 passes.
- [ ] application launch/close x20 passes.
- [ ] airplane-mode / Wi-Fi transition passes.
- [ ] Wi-Fi ↔ Ethernet transition passes when the required hardware is available; otherwise record it explicitly as not available rather than silently skipping it.

## Resource and state evidence

- [ ] active client count returns to baseline after application teardown.
- [ ] active socket count returns to baseline after churn.
- [ ] socket/client high-water marks are recorded.
- [ ] no unbounded allocation or thread growth is observed.
- [ ] no thread-per-socket behavior exists.
- [ ] context-ID exhaustion falls back to Atmosphere raw-forward rather than creating context 0 state.
- [ ] recent logs contain no credentials, VLESS URIs, Authorization values, private keys, subscription tokens, or other secrets.

## Review gate

- [ ] machine-readable hardware evidence JSON is attached to issue #3 or otherwise archived with the exact source/build identity.
- [ ] generated Markdown hardware report is attached/archived.
- [ ] independent review has no unresolved Critical findings.
- [ ] independent review has no unresolved Important findings.

The original-Switch matrix is tracked by GitHub issue #3.

## Exit condition

Phase 0 may be called complete only when:

1. GitHub host CI is green on the tested source revision;
2. issue #2 is closed with exact build evidence;
3. issue #3 is closed with the complete hardware evidence matrix;
4. independent review has no unresolved Critical/Important findings.

Until then, SOCKS5, VLESS, TLS, REALITY, Vision and DNS-tunneling implementation remain out of scope.
