#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT}/build/offline-host-tests"
CXX="${CXX:-g++}"

# Keep this list in sync with add_executable(nxless_unit_tests ...) in tests/CMakeLists.txt.
TEST_SOURCES=(
  unit/socket/socket_registry_tests.cpp
  unit/diagnostics/secret_redactor_tests.cpp
  unit/diagnostics/ring_logger_tests.cpp
  unit/config/config_tests.cpp
  unit/config/boot_policy_tests.cpp
  ../sysmodule/source/platform/compatibility.cpp
  ../sysmodule/source/boot/boot_coordinator.cpp
  unit/ipc/control_protocol_tests.cpp
  unit/ipc/control_runtime_tests.cpp
  integration/fake_bsd/fake_bsd_backend.cpp
  integration/fake_bsd/transparent_forwarding_tests.cpp
  integration/fake_bsd/fault_injection_tests.cpp
  unit/bsd/bsd_forwarder_tests.cpp
  unit/bsd/bsd_client_session_tests.cpp
  ../sysmodule/source/bsd/bsd_client_session.cpp
  ../sysmodule/source/bsd/bsd_mitm_server.cpp
  ../sysmodule/source/bsd/bsd_forwarder.cpp
)

# Keep this list in sync with add_library(nxless_common STATIC ...) in common/CMakeLists.txt.
COMMON_SOURCES=(
  src/socket/socket_registry.cpp
  src/socket/transparent_bsd_forwarder.cpp
  src/diagnostics/secret_redactor.cpp
  src/diagnostics/ring_logger.cpp
  src/config/config.cpp
  src/status/runtime_status.cpp
  src/status/boot_policy.cpp
  src/ipc/control_runtime.cpp
)

mkdir -p "${BUILD_DIR}"
SOURCES=("${ROOT}/tests/offline_shim/main.cpp")
for source in "${TEST_SOURCES[@]}"; do
  SOURCES+=("${ROOT}/tests/${source}")
done
for source in "${COMMON_SOURCES[@]}"; do
  SOURCES+=("${ROOT}/common/${source}")
done

"${CXX}" \
  -std=c++20 -O1 -g \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion \
  -DNXLESS_ENABLE_PHASE0_TEST_HOOKS=1 \
  -I"${ROOT}/tests/offline_shim" \
  -I"${ROOT}/common/include" \
  -I"${ROOT}/sysmodule/include" \
  -I"${ROOT}/tests/integration/fake_bsd" \
  "${SOURCES[@]}" -pthread \
  -o "${BUILD_DIR}/nxless-tests"

ASAN_OPTIONS="detect_leaks=1:halt_on_error=1" \
UBSAN_OPTIONS="halt_on_error=1" \
  "${BUILD_DIR}/nxless-tests"
