.PHONY: host-test host-test-offline switch switch-package phase0-build verify-locks check-title-id verify-package-policy
host-test:
	cmake --preset host-debug
	cmake --build --preset host-debug
	ctest --preset host-debug

host-test-offline:
	scripts/run-host-tests-offline.sh

switch:
	@test -n "$(DEVKITPRO)" || (echo "DEVKITPRO is not set" >&2; exit 2)
	$(MAKE) -C sysmodule NXLESS_ATMOSPHERE_ROOT="$(NXLESS_ATMOSPHERE_ROOT)"

switch-package:
	@test -n "$(DEVKITPRO)" || (echo "DEVKITPRO is not set" >&2; exit 2)
	$(MAKE) -C sysmodule dist NXLESS_ATMOSPHERE_ROOT="$(NXLESS_ATMOSPHERE_ROOT)"

phase0-build:
	python3 scripts/phase0_build.py --repo . $(if $(NXLESS_ATMOSPHERE_ROOT),--atmosphere-root "$(NXLESS_ATMOSPHERE_ROOT)",) $(if $(RECORD),--record "$(RECORD)",) $(if $(BUILDER),--builder "$(BUILDER)",) $(if $(NO_FETCH_ATMOSPHERE),--no-fetch-atmosphere,)

verify-package-policy:
	python3 scripts/verify-phase0-package.py --self-test

verify-locks:
	python3 scripts/verify-dependency-lock.py --self-test
	python3 scripts/verify-dependency-lock.py

check-title-id:
	python3 scripts/check-title-id-collision.py 0100000000004E58

.PHONY: hardware-tool-test hardware-probe-core-test hardware-probe-host-compile hardware-probe hardware-preflight hardware-new-record hardware-record-host hardware-record-build hardware-check hardware-echo

hardware-tool-test:
	python3 -m unittest discover -s tests/tooling -p 'test_*.py'
	$(MAKE) hardware-probe-core-test
	$(MAKE) hardware-probe-host-compile

hardware-probe-core-test:
	@mkdir -p build/tooling
	g++ -std=c++20 -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Werror -Itools/hardware_probe/include -Icommon/include tools/hardware_probe/tests/probe_core_tests.cpp tools/hardware_probe/source/probe_core.cpp -o build/tooling/nxless-probe-core-test
	./build/tooling/nxless-probe-core-test

hardware-probe-host-compile:
	@mkdir -p build/tooling
	g++ -std=c++20 -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Werror -Itests/tooling/libnx_shim -Itools/hardware_probe/include -Icommon/include tools/hardware_probe/source/main.cpp tools/hardware_probe/source/probe_core.cpp -o build/tooling/nxless-probe-host-compile

hardware-probe: hardware-preflight
	$(MAKE) -C tools/hardware_probe

hardware-preflight:
	python3 scripts/phase0_hardware.py preflight --repo .

hardware-new-record:
	@test -n "$(RECORD)" || (echo "RECORD=<path.json> is required" >&2; exit 2)
	python3 scripts/phase0_hardware.py new-record --repo . --output "$(RECORD)"

hardware-record-host:
	@test -n "$(RECORD)" || (echo "RECORD=<path.json> is required" >&2; exit 2)
	python3 scripts/phase0_hardware.py record-host --repo . --record "$(RECORD)"

hardware-record-build:
	@test -n "$(RECORD)" || (echo "RECORD=<path.json> is required" >&2; exit 2)
	python3 scripts/phase0_hardware.py record-build --repo . --record "$(RECORD)" $(if $(BUILDER),--builder "$(BUILDER)",)

hardware-check:
	@test -n "$(RECORD)" || (echo "RECORD=<path.json> is required" >&2; exit 2)
	python3 scripts/phase0_hardware.py check --record "$(RECORD)" --level "$(if $(LEVEL),$(LEVEL),phase0)" $(if $(REPORT),--markdown "$(REPORT)",)

hardware-echo:
	python3 scripts/phase0_hardware.py echo-server --host "$(if $(HOST),$(HOST),0.0.0.0)" --tcp-port "$(if $(TCP_PORT),$(TCP_PORT),5001)" --udp-port "$(if $(UDP_PORT),$(UDP_PORT),5002)"
