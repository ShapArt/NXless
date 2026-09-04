include(FetchContent)
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG 317ac1ed4c0bb6e6b91eafc817e05c488feffcb3
  GIT_SHALLOW FALSE
)
FetchContent_MakeAvailable(Catch2)
include(${catch2_SOURCE_DIR}/extras/Catch.cmake)

add_executable(nxless_unit_tests
  unit/socket/socket_registry_tests.cpp
  unit/diagnostics/secret_redactor_tests.cpp
  unit/diagnostics/ring_logger_tests.cpp
  unit/config/config_tests.cpp
  unit/config/boot_policy_tests.cpp
  ../sysmodule/source/platform/compatibility.cpp
  ../sysmodule/source/boot/boot_coordinator.cpp
  unit/ipc/control_protocol_tests.cpp
  unit/ipc/control_runtime_tests.cpp
  unit/ipc/control_state_tests.cpp
  integration/fake_bsd/fake_bsd_backend.cpp
  integration/fake_bsd/transparent_forwarding_tests.cpp
  integration/fake_bsd/fault_injection_tests.cpp
  unit/bsd/bsd_forwarder_tests.cpp
  unit/bsd/bsd_client_session_tests.cpp
  ../sysmodule/source/bsd/bsd_client_session.cpp
  ../sysmodule/source/bsd/bsd_mitm_server.cpp
  ../sysmodule/source/bsd/bsd_forwarder.cpp
)
target_link_libraries(nxless_unit_tests PRIVATE nxless_common Catch2::Catch2WithMain)
target_compile_options(nxless_unit_tests PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion)
catch_discover_tests(nxless_unit_tests TEST_PREFIX "socket_registry::")

target_include_directories(nxless_unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/sysmodule/include)

target_compile_definitions(nxless_unit_tests PRIVATE NXLESS_ENABLE_PHASE0_TEST_HOOKS=1)
