add_library(nxless_common STATIC
  src/socket/socket_registry.cpp
  src/socket/transparent_bsd_forwarder.cpp
  src/diagnostics/secret_redactor.cpp
  src/diagnostics/ring_logger.cpp
  src/config/config.cpp
  src/status/runtime_status.cpp
  src/status/boot_policy.cpp
  src/ipc/control_runtime.cpp
)
target_include_directories(nxless_common PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_features(nxless_common PUBLIC cxx_std_20)
target_compile_options(nxless_common PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion)
if(NXLESS_ENABLE_SANITIZERS AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(nxless_common PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(nxless_common PUBLIC -fsanitize=address,undefined)
endif()
