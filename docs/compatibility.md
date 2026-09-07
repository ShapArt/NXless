# NXless Compatibility Matrix

**Rule:** absence of evidence is not support. A combination is marked supported only after documented hardware tests.

## 1. Research/build baseline

| Component | Version | Build researched | Hardware tested | Support claim |
|---|---:|---:|---:|---|
| Horizon OS | 22.5.0 | yes | **no** | **not yet supported; Phase 0 target** |
| Atmosphère | 1.11.2 | yes | **no** | **not yet supported; Phase 0 target** |
| devkitA64 | r30 | yes | n/a | pinned build target |
| GCC | >=16.1.0 (r30 requirement) | yes | n/a | pinned through toolchain image |
| binutils | >=2.46.0 | yes | n/a | pinned through toolchain image |
| newlib | >=4.6.0.20260123-4 | yes | n/a | pinned through toolchain image |
| libnx | 4.12.0 (`7644c9b26099aa2d2145bc72a21ee24190e92085`) | yes | no | pinned Phase 0 dependency |
| libstratosphere | Atmosphère 1.11.2 / **`5388824`** | yes | no | exact Phase 0 source-tree pin |

HOS 22.5.0 updated `bsdsocket`; this makes hardware validation of transparent forwarding mandatory before claiming Phase 0 complete.

## 2. Platform scope

| Platform | Status |
|---|---|
| Original Nintendo Switch / NX family | target |
| Switch Lite / OLED (same NX software platform) | requires separate hardware entries where available |
| Switch 2 / Ounce | **unsupported/out of scope** |

Switchbrew documents command behavior that differs between NX and Ounce (for example command 36), so support is not inferred from shared version numbers.

## 3. Per-release hardware table template

Each release must append evidence such as:

| Release | HOS | Atmosphère | Hardware | Wi-Fi | Ethernet | HBMenu TCP | Game TCP A | Game TCP B | UDP game | Sleep/wake | AP change | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pre-0.1 Phase 0 | 22.5.0 | 1.11.2 | original Switch | pending | pending | pending | pending | pending | n/a | pending | pending | **pending** |

No `PASS` is entered from a host simulation; hardware rows require actual console evidence.

## 4. Lifecycle checklist required per supported combination

- cold boot with NXless enabled;
- cold boot with `disable.flag`;
- launch/close HBMenu networking app;
- launch/close representative game;
- HOME suspend/resume;
- sleep for short and long intervals;
- wake and reuse/new socket creation;
- Wi-Fi disconnect/reconnect;
- AP change;
- airplane mode on/off;
- Wi-Fi -> dock Ethernet;
- dock Ethernet -> Wi-Fi;
- proxy outage during active connection;
- proxy recovery;
- SD read failure/corrupt config scenario;
- high socket churn;
- concurrent sockets;
- uninstall/reboot.

## 5. Traffic-scope matrix

This matrix is intentionally conservative until observed:

| Path | MVP expectation | Evidence required |
|---|---|---|
| `bsd:u` TCP | target | Phase 0/1 hardware tests |
| `bsd:u` UDP | later | UDP Associate design + hardware |
| `bsd:s` | no MITM | privileged-risk research |
| `bsd:a` | no MITM | privileged-risk research |
| `sfdnsres` | System DNS | DNS research phase |
| raw sockets / ICMP | not claimed | dedicated tests |
| Nintendo system services | not claimed globally | service-by-service tests |
| background/system traffic | not claimed | service-by-service tests |

## 6. Dependency admission status

| Dependency | Version researched | Phase | Status |
|---|---:|---|---|
| Borealis | current main, Apache-2.0, repository warns WIP | GUI | candidate; exact commit must be build-tested before admission |
| libultrahand | v2.5.3 / `856ddbd` | overlay | candidate; optional |
| devkitPro switch-mbedtls | 2.28.10 | TLS | **rejected for new production TLS: upstream branch EOL** |
| Mbed TLS | 4.1.1 LTS | TLS | candidate for Switch port/adaptor; not yet hardware-supported |
| Xray-core | v26.7.28 / `5ca6f4b` | host oracle | pinned test peer/reference only |

## 7. Version policy

A HOS or Atmosphère update does **not** inherit support automatically.

For every new HOS:

1. inspect Switchbrew system-title diff, especially `bsdsocket`, `ssl`, `wlan`, `am`;
2. compare socket IPC command/structure definitions;
3. rebuild against the pinned/updated toolchain in a feature branch;
4. run host tests;
5. boot with `disable.flag` and then normal mode;
6. execute hardware smoke/lifecycle matrix;
7. only then add the combination to the supported release table.

## Sources

- HOS 22.5.0: https://switchbrew.org/wiki/22.5.0
- Atmosphère 1.11.2 release: https://github.com/Atmosphere-NX/Atmosphere/releases
- libnx releases: https://github.com/switchbrew/libnx/releases
- devkitA64 r30 packaging: https://github.com/devkitPro/pacman-packages/commit/f103fe8
- Mbed TLS support: https://github.com/Mbed-TLS/mbedtls/blob/development/BRANCHES.md
