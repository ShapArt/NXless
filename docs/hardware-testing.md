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

Schema v3 intentionally leaves console HOS/Atmosphere identity unobserved. The record is tied to the source revision; do not copy a record from another commit and do not fill observed console identity by editing JSON manually.

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
2. Copy the separately verified `NXlessProbe.nro` to the Homebrew Menu location used for test tools.
3. Make sure `/atmosphere/contents/0100000000004E58` is absent for the baseline run. If an older NXless copy exists, remove only that program directory while powered off.
4. Do not copy the new sysmodule package yet; first capture the no-NXless baseline in step 7.
5. After the baseline is recorded, power off and copy only the verified Phase 0 package layout to the SD card.
6. Confirm `/config/nxless/` exists and make the first NXless boot with `/config/nxless/disable.flag` present.
7. Never modify NAND or Nintendo system files for NXless recovery.

See `docs/recovery.md` for the recovery procedure.

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

Use the actual model/revision, SD description and network used for the matrix.

## 6. Start the host echo endpoints

On a machine reachable by the Switch:

```sh
python3 scripts/phase0_hardware.py echo-server --host 0.0.0.0 --tcp-port 5001 --udp-port 5002
```

Use the machine's LAN IPv4 literal in the probe configuration. Phase 0 deliberately does not use DNS as part of this test.

## 7. Capture the literal no-NXless network baseline

With `/atmosphere/contents/0100000000004E58` absent, run `NXlessProbe`. Copy the exact `Echo target ...` and final `Summary: ...` lines from the screen. A valid baseline must report `ctl=UNAVAILABLE`; `disable.flag` is not an acceptable substitute because the NXless control service still exists in that mode.

```sh
python3 scripts/phase0_hardware.py record-network --record evidence/phase0.json --mode baseline \
  --echo-line "Echo target 192.0.2.10 TCP:5001 UDP:5002 concurrency:4" \
  --summary-line "Summary: ctl=UNAVAILABLE tcp=PASS udp=PASS"
```

The values above show only the required CLI shape. Replace them with the exact two lines printed by the tested console. The parser accepts an IPv4 literal only and a probe concurrency within the compiled Phase 0 maximum of 16.

After recording the baseline, power the console off and install the exact verified NXless package as described in step 4. Do not edit `network.tcp`, `network.udp`, or the captured probe fields in JSON by hand.

## 8. Recovery, cold-boot and transparent-MITM matrix

Required minimums:

- `disable.flag`: 10 cold boots
- transparent MITM enabled: 20 cold boots

Record every attempt, including failures:

```sh
python3 scripts/phase0_hardware.py record-boot --record evidence/phase0.json --mode disable --cold-boot pass --home pass --network pass --ctl-status SafeDisabled
python3 scripts/phase0_hardware.py record-boot --record evidence/phase0.json --mode mitm --cold-boot pass --home pass --network pass --ctl-status DisconnectedPassthrough
```

After the required transparent-MITM boots, run `NXlessProbe` against the same echo target and concurrency used for the baseline. Copy the exact two lines again. A valid NXless run must report `ctl=PASS` and both echo tests must pass:

```sh
python3 scripts/phase0_hardware.py record-network --record evidence/phase0.json --mode nxless \
  --echo-line "Echo target 192.0.2.10 TCP:5001 UDP:5002 concurrency:4" \
  --summary-line "Summary: ctl=PASS tcp=PASS udp=PASS"
```

The baseline and NXless runs must use the same IPv4 target, ports and concurrency. The validator re-parses both captured lines and rejects missing provenance, mismatches, `ctl=ERROR`, a baseline that still exposes `nxl:ctl`, or failed TCP/UDP echo results.

Also prove directory-removal recovery after NXless has actually been installed: power off, remove only `/atmosphere/contents/0100000000004E58`, boot, verify HOME and normal networking, and record the result:

```sh
python3 scripts/phase0_hardware.py record-recovery --record evidence/phase0.json --powered-off pass --removed-only-program-dir pass --boot pass --network pass
```

Restore the same verified candidate package before continuing the remaining NXless lifecycle matrix.

## 9. Lifecycle and session-admission matrix

Record the required transitions with `record-lifecycle`:

- HOME/resume x2
- sleep/wake x20
- Wi-Fi off/on x10
- access-point change x5
- application launch/close x20
- airplane-mode/Wi-Fi transition
- Wi-Fi/Ethernet transitions when the hardware is available

First record whether Ethernet transition testing is available:

```sh
python3 scripts/phase0_hardware.py record-ethernet-availability --record evidence/phase0.json --available no
```

If it is available, set `--available yes` and record both directions with `record-lifecycle`.

Example lifecycle attempt:

```sh
python3 scripts/phase0_hardware.py record-lifecycle --record evidence/phase0.json --kind sleep_wake --result pass
```

Issue #3 separately requires repeated `bsd:u` client/session churn without crossing Atmosphere's fatal SM acknowledgement boundary. Record each admission trial; at least two clean trials are required by the machine validator to prove repetition:

```sh
python3 scripts/phase0_hardware.py record-session-admission --record evidence/phase0.json --result pass --sm-ack-abort no
python3 scripts/phase0_hardware.py record-session-admission --record evidence/phase0.json --result pass --sm-ack-abort no
```

If an acknowledgement abort or any other admission fatal is observed, record it immediately instead of hiding it:

```sh
python3 scripts/phase0_hardware.py record-failure --record evidence/phase0.json --kind sm-ack-abort --details "Exact observed fatal/context"
```

Any entry under `failures` blocks the hardware verdict until a new investigated/fixed build produces a fresh evidence record.

## 10. Real applications

At least two different real networked applications or games must preserve their baseline behavior.

```sh
python3 scripts/phase0_hardware.py record-app --record evidence/phase0.json --title "Application A" --baseline pass --nxless pass
python3 scripts/phase0_hardware.py record-app --record evidence/phase0.json --title "Application B" --baseline pass --nxless pass
```

Use the actual application titles in the evidence record.

## 11. Resource and diagnostics evidence

Record heap, handle and bounded-growth observations after the lifecycle/churn matrix:

```sh
python3 scripts/phase0_hardware.py record-resources --record evidence/phase0.json --private-heap-bytes 2097152 --peak-heap-bytes 2097152 --registry-leak-detected no --unbounded-growth-detected no
```

The heap values above are examples of the CLI shape, not expected measurements. Record the observed values from the tested build.

SocketRegistry client/socket high-water marks have a single evidence source: the exact `nxl:ctl` status line printed by `NXlessProbe`. After the lifecycle/churn matrix, run `NXlessProbe` again against the same echo endpoints and copy the full line shown under `Status after socket tests:`. Record that line verbatim:

```sh
python3 scripts/phase0_hardware.py record-registry-telemetry \
  --record evidence/phase0.json \
  --status-line "clients=0 client-high-water=4 sockets=0 socket-high-water=16 dropped-logs=0 last-error=0"
```

The status line above is only an example of the required format. Replace it with the exact line from the tested console. Do not manually enter or edit `peak_clients` or `peak_sockets`; `record-registry-telemetry` parses the captured line and writes those fields itself. The hardware validator rejects missing telemetry, malformed telemetry, or peak values that do not match the captured line.

Review recent diagnostics/log output for credentials, tokens, proxy URIs, private keys or other secrets, then record the result explicitly:

```sh
python3 scripts/phase0_hardware.py record-diagnostics --record evidence/phase0.json --recent-logs-secret-free yes --notes "Reviewed recent Phase 0 diagnostics"
```

A missing or failed secret review blocks the hardware verdict.

## 12. Independent review

After hardware testing and source review:

```sh
python3 scripts/phase0_hardware.py record-review --record evidence/phase0.json --reviewer "reviewer" --date 2026-09-05 --critical 0 --important 0
```

Use the real reviewer identity/date. A nonzero unresolved Critical or Important count blocks Phase 0 completion.

## 13. Generate the verdict

```sh
python3 scripts/phase0_hardware.py check --record evidence/phase0.json --level phase0 --markdown evidence/phase0.md
```

A passing result must be attached to issue #3 together with the JSON record, Markdown report, package SHA-256, probe SHA-256 and the exact source revision. An anecdotal "it boots" result is not sufficient.

## Failure handling

If any boot, network, lifecycle, session-admission or recovery step fails:

1. keep the failed evidence entry;
2. add a `record-failure` entry for any crash/fatal or admission-boundary event;
3. restore `disable.flag` or remove only `/atmosphere/contents/0100000000004E58` while powered off;
4. collect sanitized diagnostics;
5. reproduce before changing code;
6. fix through the normal test/review/CI path;
7. produce a new package, probe and evidence record tied to the new commit.

Do not continue to SOCKS5/VLESS while the Phase 0 hardware gate is red.
