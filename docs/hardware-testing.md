# Phase 0 hardware testing

This document is the operator runbook for the NXless Phase 0 hardware gate. Phase 1A must not start until the machine-readable record reaches a clean `phase0` verdict.

## Required baseline

- Original Nintendo Switch hardware
- Horizon OS 22.5.0
- Atmosphere 1.11.2 at `5388824be146a89619e8d641acd64599cf1c5f62`
- devkitA64 r30
- libnx package 4.12.0-1
- NXless Program ID `0100000000004E58`
- a clean source tree from the same revision used for both the sysmodule and `NXlessProbe.nro`

Issue #2 tracks the exact Switch build. Issue #3 tracks this hardware matrix.

## 1. Preflight the build host

From the repository root:

```sh
python3 scripts/phase0_hardware.py preflight --repo .
```

Do not continue with a release candidate if the exact toolchain, pinned Atmosphere source, or clean-tree checks fail.

## 2. Create and populate the evidence record

```sh
python3 scripts/phase0_hardware.py new-record --repo . --output evidence/phase0.json
python3 scripts/phase0_hardware.py record-host --repo . --record evidence/phase0.json
```

Schema v4 intentionally leaves console HOS/Atmosphere identity unobserved. It also refuses unverifiable operator-entered heap byte counts. The record is tied to the source revision; do not copy a record from another commit and do not fill observed fields by editing JSON manually.

## 3. Produce the exact Switch build and bind the probe

Use the repository build gate rather than invoking the sysmodule linker ad hoc:

```sh
make phase0-build RECORD=evidence/phase0.json
python3 scripts/phase0_hardware.py record-probe-build --repo . --record evidence/phase0.json
```

Alternatively, if host verification was already recorded:

```sh
python3 scripts/phase0_hardware.py record-build --repo . --record evidence/phase0.json --builder "$USER"
python3 scripts/phase0_hardware.py record-probe-build --repo . --record evidence/phase0.json
```

The evidence record must contain both `build.package_sha256` and `build.probe_sha256`, and `build.probe_source_commit` must equal the package source commit. `NXlessProbe.nro` is test-only and must never be added to the Phase 0 release ZIP.

## 4. Prepare the SD card safely

Keep recovery available before the first enabled boot. The literal network baseline must be taken with NXless absent, not merely disabled.

1. Power the console off completely.
2. Copy the separately verified `NXlessProbe.nro` to `sdmc:/switch/NXlessProbe/NXlessProbe.nro`.
3. Put its config at `sdmc:/switch/NXlessProbe/probe.ini`.
4. Make sure `/atmosphere/contents/0100000000004E58` is absent for the baseline run. If an older NXless copy exists, remove only that program directory while powered off.
5. Do not copy the new sysmodule package yet; first capture the no-NXless baseline in step 7.
6. After the baseline is recorded, power off and copy only the verified Phase 0 package layout to the SD card.
7. Confirm `/config/nxless/` exists and make the first NXless boot with `/config/nxless/disable.flag` present.
8. Never modify NAND or Nintendo system files for NXless recovery.

See `docs/recovery.md` for the recovery procedure.

### NXlessProbe configuration

The probe reads exactly `sdmc:/switch/NXlessProbe/probe.ini`:

```ini
host=192.168.1.10
tcp_port=5001
udp_port=5002
concurrent=4
```

Use the actual LAN IPv4 address of the PC running the echo server. DNS names are intentionally rejected. `concurrent` must be between 1 and 16. Keep the same host, ports, and concurrency for baseline and NXless runs.

## 5. Record the actual console identity and HBMenu baseline

Record what is actually shown/installed on the test console, not the target values from the build record. The HBMenu baseline here is taken while the NXless sysmodule is absent:

```sh
python3 scripts/phase0_hardware.py record-console \
  --record evidence/phase0.json \
  --model "HAC-001" \
  --hos 22.5.0 \
  --atmosphere-version 1.11.2 \
  --atmosphere-commit 5388824 \
  --sd-filesystem-capacity "256 GB" \
  --network "Wi-Fi, test LAN" \
  --hbmenu-tcp-baseline pass \
  --hbmenu-udp-baseline pass
```

Use the actual model/revision, SD description, and network used for the matrix. If the observed HOS or Atmosphere identity differs from the admitted stack, record the real value and stop this candidate rather than substituting the expected value.

## 6. Start the host echo endpoints

On a machine reachable by the Switch:

```sh
python3 scripts/phase0_hardware.py echo-server --host 0.0.0.0 --tcp-port 5001 --udp-port 5002
```

Allow inbound TCP 5001 and UDP 5002 from the Switch test LAN if the host firewall requires it.

## 7. Capture the literal no-NXless network baseline

With `/atmosphere/contents/0100000000004E58` absent, run `NXlessProbe`. Copy the exact `Echo target ...` and final `Summary: ...` lines from the screen. A valid baseline must report `ctl=UNAVAILABLE`; `disable.flag` is not an acceptable substitute because the NXless control service still exists in that mode.

```sh
python3 scripts/phase0_hardware.py record-network --record evidence/phase0.json --mode baseline \
  --echo-line "Echo target 192.168.1.10 TCP:5001 UDP:5002 concurrency:4" \
  --summary-line "Summary: ctl=UNAVAILABLE tcp=PASS udp=PASS"
```

The values above show only the CLI shape. Replace them with the exact two lines printed by the tested console. After recording the baseline, power off and install the exact verified NXless package. Do not edit `network.tcp`, `network.udp`, or captured probe fields in JSON by hand.

## 8. Recovery, cold-boot, and transparent-MITM matrix

Required minimums:

- `disable.flag`: 10 cold boots
- transparent MITM enabled: 20 cold boots

Record every attempt, including failures:

```sh
python3 scripts/phase0_hardware.py record-boot --record evidence/phase0.json --mode disable --cold-boot pass --home pass --network pass --ctl-status SafeDisabled
python3 scripts/phase0_hardware.py record-boot --record evidence/phase0.json --mode mitm --cold-boot pass --home pass --network pass --ctl-status DisconnectedPassthrough
```

Do not hide or delete a failed attempt to make the count green.

After the required transparent-MITM boots, run `NXlessProbe` against the same echo target and concurrency used for the baseline. A valid NXless run must report `ctl=PASS` and both echo tests must pass:

```sh
python3 scripts/phase0_hardware.py record-network --record evidence/phase0.json --mode nxless \
  --echo-line "Echo target 192.168.1.10 TCP:5001 UDP:5002 concurrency:4" \
  --summary-line "Summary: ctl=PASS tcp=PASS udp=PASS"
```

The validator re-parses both captured lines and rejects missing provenance, mismatched host/ports/concurrency, `ctl=ERROR`, a baseline that exposes `nxl:ctl`, or failed TCP/UDP echo results.

Also prove directory-removal recovery after NXless has actually been installed: power off, remove only `/atmosphere/contents/0100000000004E58`, boot, verify HOME and normal networking, and record the result:

```sh
python3 scripts/phase0_hardware.py record-recovery --record evidence/phase0.json --powered-off pass --removed-only-program-dir pass --boot pass --network pass
```

Restore the same verified candidate package before continuing the remaining NXless lifecycle matrix.

## 9. Lifecycle and session-admission matrix

Required transitions:

- HOME/resume x2
- sleep/wake x20
- Wi-Fi off/on x10
- access-point change x5
- application launch/close x20
- airplane-mode/Wi-Fi transition x1
- Wi-Fi/Ethernet and Ethernet/Wi-Fi x1 each when hardware is available

First record Ethernet availability:

```sh
python3 scripts/phase0_hardware.py record-ethernet-availability --record evidence/phase0.json --available no
```

If available, use `yes` and record both directions.

Exact lifecycle kinds are:

- `home_resume`
- `sleep_wake`
- `wifi_cycle`
- `ap_change`
- `airplane_wifi`
- `wifi_ethernet`
- `ethernet_wifi`
- `app_launch_close`

Example:

```sh
python3 scripts/phase0_hardware.py record-lifecycle --record evidence/phase0.json --kind sleep_wake --result pass
```

Issue #3 separately requires repeated `bsd:u` client/session churn without crossing Atmosphere's fatal SM acknowledgement boundary. At least two clean trials are required:

```sh
python3 scripts/phase0_hardware.py record-session-admission --record evidence/phase0.json --result pass --sm-ack-abort no
python3 scripts/phase0_hardware.py record-session-admission --record evidence/phase0.json --result pass --sm-ack-abort no
```

If an acknowledgement abort or any other admission fatal is observed, record it immediately:

```sh
python3 scripts/phase0_hardware.py record-failure --record evidence/phase0.json --kind sm-ack-abort --details "Exact observed fatal/context"
```

Any entry under `failures` blocks the hardware verdict until an investigated/fixed build produces a fresh evidence record.

## 10. Real applications

At least two different real networked applications or games must preserve their baseline behavior:

```sh
python3 scripts/phase0_hardware.py record-app --record evidence/phase0.json --title "Application A" --version "actual" --baseline pass --nxless pass
python3 scripts/phase0_hardware.py record-app --record evidence/phase0.json --title "Application B" --version "actual" --baseline pass --nxless pass
```

Use the actual application titles and versions where available.

## 11. Resource and diagnostics evidence

### What Phase 0 can honestly prove

The Phase 0 sysmodule allocator capacity is a fixed 2 MiB buffer in `sysmodule/source/main.cpp`. Its exact source shape is protected by `tests/tooling/test_phase0_allocator_bound_contract.py`.

Phase 0 does **not** claim a measured runtime private-heap or peak-heap byte count: neither `nxl:ctl` nor `NXlessProbe` exposes such telemetry. Schema v4 therefore does not ask the operator to invent those numbers.

Runtime resource evidence is instead based on:

1. exact `nxl:ctl` SocketRegistry telemetry;
2. the enforced client/socket limits;
3. repeated lifecycle/session churn;
4. an explicit observation that no registry leak or unbounded growth was detected.

After the lifecycle/churn matrix, run `NXlessProbe` again against the same echo endpoints. Copy the full line shown under `Status after socket tests:` and record it verbatim:

```sh
python3 scripts/phase0_hardware.py record-registry-telemetry \
  --record evidence/phase0.json \
  --status-line "clients=0 client-high-water=4 sockets=0 socket-high-water=16 dropped-logs=0 last-error=0"
```

The status line above is only an example of the required syntax. Replace it with the exact line from the tested console. Do not manually enter or edit `peak_clients` or `peak_sockets`; `record-registry-telemetry` derives them from the captured line. The hardware validator rejects missing or malformed telemetry, mismatched peaks, client high-water above 64, or socket high-water above 512.

Then record the bounded-growth conclusion from the completed matrix:

```sh
python3 scripts/phase0_hardware.py record-resources \
  --record evidence/phase0.json \
  --registry-leak-detected no \
  --unbounded-growth-detected no \
  --notes "Observed stable registry state across lifecycle/session churn"
```

If a leak or unbounded growth is observed, record `yes`; that blocks acceptance and must be investigated. Do not convert an observed failure to `no` merely to satisfy the validator.

Review recent diagnostics/log output for credentials, tokens, proxy URIs, private keys, or other secrets, then record the result explicitly:

```sh
python3 scripts/phase0_hardware.py record-diagnostics --record evidence/phase0.json --recent-logs-secret-free yes --notes "Reviewed recent Phase 0 diagnostics"
```

A missing or failed secret review blocks the hardware verdict.

## 12. Independent review

After hardware testing and source review:

```sh
python3 scripts/phase0_hardware.py record-review --record evidence/phase0.json --reviewer "reviewer" --date YYYY-MM-DD --critical 0 --important 0
```

Use the real independent reviewer identity/date. Author/coordinator self-review does not satisfy this gate. A nonzero unresolved Critical or Important count blocks Phase 0 completion.

## 13. Generate the verdict

```sh
python3 scripts/phase0_hardware.py check --record evidence/phase0.json --level phase0 --markdown evidence/phase0.md
```

A passing result must be attached to Issue #3 together with the JSON record, Markdown report, package SHA-256, probe SHA-256, and exact source revision. An anecdotal "it boots" result is not sufficient.

## Failure handling

If any boot, network, lifecycle, session-admission, recovery, resource, or diagnostics step fails:

1. keep the failed evidence entry;
2. add a `record-failure` entry for any crash/fatal or admission-boundary event;
3. restore `disable.flag` or remove only `/atmosphere/contents/0100000000004E58` while powered off;
4. collect sanitized diagnostics;
5. reproduce before changing code;
6. fix through the normal TDD/review/CI path;
7. produce a new package, probe, and evidence record tied to the new commit.

Do not continue to SOCKS5/VLESS while the Phase 0 hardware gate is red.
