# NXless Architecture

**Status:** Phase 0 pre-hardware design baseline  
**Target:** original Nintendo Switch / NX, HOS 22.5.0, Atmosphere 1.11.2

## Product definition

NXless is initially defined as a **system-wide TCP/UDP proxy/tunnel for compatible Horizon applications using intercepted BSD socket services**. It is not described as a packet-level VPN.

The selected path is:

```text
Horizon application
  -> bsd:u IPC
  -> nxless-sys MITM
  -> transparent/direct path in Phase 0
  -> routing policy in later phases
  -> SOCKS5 TCP first
  -> native VLESS/TLS/REALITY only after the interception layer is proven
```

## Phase 0 boundary

Phase 0 does not implement SOCKS5, VLESS, TLS, DNS tunneling, packet interception, GUI, or overlay functionality. Its purpose is to prove that `bsd:u` interception can coexist with ordinary Horizon applications without changing baseline networking behavior.

The pinned research/build target is:

- HOS 22.5.0
- Atmosphere 1.11.2 / `5388824`
- devkitA64 r30
- libnx 4.12.0 build baseline / `7644c9b26099aa2d2145bc72a21ee24190e92085`
- Program ID `0100000000004E58`

No other HOS/Atmosphere combination inherits support automatically.

## Components

The implementation is split into a host-testable portable core and thin Horizon adapters.

Portable core responsibilities:

- bounded `SocketRegistry` keyed by client context + fd + generation;
- transparent BSD forwarding contract;
- bounded diagnostics ring and centralized secret redaction;
- safe config parsing;
- versioned control DTOs/status;
- pure boot/recovery policy.

Horizon-specific responsibilities:

- `BsdMitmServer` / `BsdClientSession`;
- original-service BSD forwarding;
- `nxl:ctl` read-only service;
- SD recovery/config access;
- HOS compatibility gate;
- sysmodule startup and process configuration.

## BSD MITM strategy

NXless MITMs `bsd:u` only. Typed hooks are deliberately restricted to fd-lifecycle operations needed for state accounting:

- `Socket`
- `SocketExempt`
- `Accept`
- `Close`

Other commands are left to Atmosphere's MITM raw-forward path so newer or less-understood command shapes are not reserialized by NXless unnecessarily.

Internal proxy work in future phases must use the original/direct BSD path rather than re-entering the intercepted route pipeline. Recursion bypass is architectural, not a destination-IP exception.

## DNS

Phase 0 reports **DNS: System**. Horizon name resolution is separate from `bsd:u`, and Atmosphere already has its own resolver MITM. NXless therefore makes no DNS-confidentiality or reliable domain-routing claim until a separate compatibility phase is completed.

## Safe boot

Startup is conservative:

1. establish minimal runtime state;
2. probe `/config/nxless/disable.flag`;
3. load validated config or safe defaults;
4. create and publish `nxl:ctl` only after its worker resources exist;
5. verify the pinned HOS gate;
6. only then allow `bsd:u` MITM registration;
7. remain disconnected/fail-open.

Ordinary SD/config errors must not become a boot-time fatal path.

## Resource policy

Initial engineering budget:

- target private heap <= 6 MiB;
- architecture review required before exceeding 8 MiB;
- bounded socket registry;
- 256 KiB diagnostics ring;
- no thread-per-socket design.

## Phase ordering

```text
Phase 0  transparent bsd:u MITM + hardware proof
Phase 1A SOCKS5 TCP
Phase 1B nonblocking/readiness correctness + UDP research
Phase 2  native VLESS/TCP
Phase 3  TLS / REALITY / Vision interoperability
Later    DNS/routing/UI/overlay polish
```

Phase 1 is blocked until the Phase 0 hardware acceptance matrix passes.
