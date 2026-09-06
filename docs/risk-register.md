# NXless Phase 0 risk register

This register tracks risks that can invalidate the Phase 0 safety claim or block admission to Phase 1A.

| ID | Risk | Impact | Current mitigation / evidence | Exit condition |
| --- | --- | --- | --- | --- |
| R-01 | `bsd:u` MITM causes a boot loop or breaks baseline networking | Critical | fail-open admission policy, `disable.flag`, removable Atmosphere contents directory, no NAND modification | issue #3 cold-boot/recovery/network matrix passes |
| R-02 | libstratosphere aborts while acknowledging a MITM session | Critical | pinned Atmosphere review confirms `Server::AcknowledgeMitmSession()` uses `R_ABORT_UNLESS(sm::mitm::AcknowledgeSession(...))`; NXless does not falsely classify this as a recoverable application error | original-hardware testing exercises repeated session churn; any observed SM-ack failure blocks release and is investigated upstream/architecturally |
| R-03 | HOS BSD command/wire drift causes incompatibility | High | Phase 0 admits only HOS 22.5.0; typed hooks limited to 2/3/12/26; other commands use Atmosphere raw-forward behavior | exact HOS 22.5.0 hardware baseline passes; new HOS versions remain disabled until separately researched |
| R-04 | Horizon/CMIF transport failure is mistaken for BSD `ret/errno` | High | fixed by `BsdForwardResult`; original platform Result is propagated through typed MITM handlers; RED→GREEN CI covers platform-failed socket/close state | canonical/offline tests remain green on hardware-tested revision |
| R-05 | client-context exhaustion creates untracked socket state | High | context 0 is invalid; exhausted allocator creates raw-passthrough-only session; registry rejects client 0 | context exhaustion host test + hardware churn show no untracked state |
| R-06 | socket/session teardown leaves stale fd state and later collides with fd reuse | High | `(client, fd, generation)` identity, bounded registry, session-destructor cleanup; BSD-level `Close` relinquishes tracking while platform-failed `Close` preserves state | app churn/resource counters in issue #3 return to baseline |
| R-07 | sysmodule resource pressure destabilizes HOS | High | no thread-per-socket, 15 BSD sessions, zero domain storage, 512 tracked sockets, 256 KiB log ring, 2 MiB allocator arena | original-hardware high-water marks remain bounded with no progressive growth |
| R-08 | malformed/oversized/unreadable SD config causes fatal startup | High | result-returning libnx FS path, 64 KiB config cap, missing config allowed, unreadable recovery probe disables MITM | recovery/error cases pass hardware testing |
| R-09 | secrets leak into logs or evidence | High | centralized `SecretRedactor`, bounded diagnostics, no persistent logging by default, package policy rejects secret-bearing artifacts | hardware evidence/log review finds no credential material |
| R-10 | build is produced with a different toolchain than the researched ABI/runtime | High | exact toolchain/source gates; no rolling devkitPro CI accepted | issue #2 closes with devkitA64 r30 / libnx 4.12.0-1 / Atmosphere `5388824` build evidence |
| R-11 | users assume DNS is tunneled/protected by BSD interception | Medium | Phase 0 explicitly reports system DNS and makes no DNS-protection claim | separate DNS design/test milestone before any protected-DNS claim |
| R-12 | host tests are mistaken for Switch compatibility evidence | High | canonical + offline host CI are necessary but not sufficient; PR remains draft and Phase 1 blocked | issues #2 and #3 both close with exact build + original-hardware evidence |

## Upstream fatal boundary

`libstratosphere` at the pinned Atmosphere revision implements MITM session acknowledgement with an aborting assertion around `sm::mitm::AcknowledgeSession`. NXless cannot turn that internal library invariant into a recoverable `Result` without replacing or patching the server-manager path.

For Phase 0 we therefore distinguish:

- **NXless-controlled ordinary failures** (SD/config compatibility/control registration/original BSD command dispatch) — designed to return/fail open where possible;
- **upstream libstratosphere invariants** — documented fatal boundaries that must be exercised by hardware testing and treated as release blockers if observed.

This distinction prevents the project from making an unqualified “cannot boot-loop/fatal” claim that the pinned framework itself does not guarantee.
