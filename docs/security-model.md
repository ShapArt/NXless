# NXless Security Model

**Scope:** Phase 0 and constraints that later proxy/tunnel phases must preserve.

## Security goals

NXless is a boot-resident networking component, so console stability and recoverability are security properties, not just UX concerns.

Primary goals:

- ordinary config, SD, network, or upstream failures must not cause a boot loop;
- boot starts disconnected and fail-open;
- `disable.flag` provides an SD-card recovery path;
- no NAND/system-file modification;
- no telemetry, analytics, ads, or mandatory NXless backend;
- secrets never appear in normal logs or diagnostic bundles;
- remote-controlled parsers remain bounded;
- dependencies and build inputs are pinned and reviewed before admission.

## Trust boundaries

### Horizon applications

Applications are untrusted clients of the intercepted `bsd:u` service. Integer fds are not globally unique, so socket identity is scoped by MITM client context and generation.

### Original BSD service

The Nintendo BSD service is the authoritative endpoint for Phase 0 socket operations. Transparent forwarding must preserve return values and BSD errno semantics.

### NXless control plane

`nxl:ctl` is versioned. Phase 0 exposes read-only version, compatibility, runtime status, and bounded recent logs. Mutation commands are intentionally absent.

### SD card

The SD card is configuration/recovery storage, **not secure secret storage**. A user with SD access can read or alter files. Later secret-bearing profile formats must document this limitation explicitly.

## Fail-open boot policy

Before installing the BSD MITM, NXless verifies:

1. recovery-file state can be safely inspected;
2. config can be parsed or safe defaults selected;
3. the control service has usable worker resources and is actually published;
4. the HOS version matches the admitted compatibility baseline.

If those gates fail, BSD interception remains disabled. Unknown/unsupported HOS versions are control-only, not “best effort”.

## Recovery

The primary recovery mechanism is:

`/config/nxless/disable.flag`

When present, NXless must not activate BSD interception. If necessary, removing `/atmosphere/contents/0100000000004E58` restores the pre-NXless sysmodule set.

Recovery behavior is not considered proven until repeated cold-boot hardware testing passes.

## Logging and diagnostics

The diagnostics subsystem is bounded in memory. Persistent SD logging is not a Phase 0 default.

A centralized `SecretRedactor` removes or masks credential-bearing material including VLESS URIs, Authorization values, userinfo, and common secret query keys. Raw config/subscription payloads must never be emitted as diagnostics.

## Memory and parsing

- socket state is bounded;
- diagnostics storage is bounded;
- config size is capped;
- IPC output arrays are capped;
- no thread-per-socket architecture;
- malformed input returns typed/safe errors where recovery is possible.

Later remote protocol parsers require fuzzing and allocation/length caps before Switch admission.

## Kill Switch

A Kill Switch is **not** a boot policy. It can only become active after an explicit user Connect action in later phases.

When enabled in a future proxy phase:

- traffic whose route decision is `PROXY` fails closed when the tunnel is unavailable;
- `DIRECT` traffic continues;
- the user must retain a recoverable control path.

## Cryptography

Phase 0 contains no TLS or VLESS implementation.

For later TLS/REALITY phases:

- certificate/public-key verification is mandatory;
- no insecure fallback;
- cryptographic RNG uses a Horizon-supported secure source;
- time-dependent verification must fail safely;
- REALITY interoperability is a separate admission milestone;
- Xray-core is used as an interoperability/reference oracle, not ported wholesale into the sysmodule.

The devkitPro `switch-mbedtls` 2.28.x line is not accepted as a new production TLS baseline because upstream 2.28 is EOL.

## Supply chain

Dependencies/actions/toolchains are pinned. Current Phase 0 verification records exact Atmosphere/libnx/Catch2/CI pins and validates package contents before release-like output is accepted.

A green host build does not imply a supported Switch release: hardware boot/lifecycle evidence remains mandatory.
