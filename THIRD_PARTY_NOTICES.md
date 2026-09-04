# Third-party notices

NXless Phase 0 references and/or integrates with the following upstream projects for documented behavior, build integration, testing, and interoperability research.

| Dependency / reference | Role in NXless | License | Phase 0 distribution note |
| --- | --- | --- | --- |
| Atmosphere / libstratosphere | Sysmodule framework, MITM/service APIs, Horizon integration | GPL-2.0 | Pinned source dependency; not vendored into release ZIP |
| libnx | Horizon/libnx APIs and toolchain package | ISC | Toolchain/runtime development dependency |
| Catch2 | Host test framework | BSL-1.0 | CI/test-only; pinned by exact commit |
| ryu_ldn_nx | Architectural reference for `bsd:u` MITM patterns | GPL-2.0 | Reference only; no source copied into NXless |
| Xray-core | Future protocol/interoperability reference | MPL-2.0 | Not part of Phase 0 runtime |
| actions/checkout | GitHub Actions checkout step | MIT | CI-only; exact SHA pinned |
| actions/upload-artifact | GitHub Actions evidence artifact transport | MIT | CI-only; exact SHA pinned |
| CMake | Host build/test tooling | BSD-3-Clause | Build/CI-only; exact version and archive checksum pinned |

Exact dependency and CI pins live in `third_party/locks/` and are checked by `scripts/verify-dependency-lock.py`.

No Xray-core or ryu_ldn_nx source code is copied into the current NXless Phase 0 implementation.
