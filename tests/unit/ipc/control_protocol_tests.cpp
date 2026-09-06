#include <catch2/catch_test_macros.hpp>
#include <nxless/ipc/control_protocol.hpp>
#include <nxless/status/runtime_status.hpp>
#include <nxless/socket/socket_registry.hpp>
#include <nxless/diagnostics/ring_logger.hpp>
#include <type_traits>

using namespace nxless;

TEST_CASE("phase0 control DTOs are trivial standard layout", "[ipc]") {
    STATIC_REQUIRE(std::is_trivial_v<ipc::VersionInfo>);
    STATIC_REQUIRE(std::is_trivially_copyable_v<ipc::VersionInfo>);
    STATIC_REQUIRE(std::is_standard_layout_v<ipc::VersionInfo>);
    STATIC_REQUIRE(std::is_trivial_v<ipc::CompatibilityInfo>);
    STATIC_REQUIRE(std::is_trivially_copyable_v<ipc::CompatibilityInfo>);
    STATIC_REQUIRE(std::is_standard_layout_v<ipc::CompatibilityInfo>);
    STATIC_REQUIRE(std::is_trivial_v<ipc::RuntimeStatus>);
    STATIC_REQUIRE(std::is_trivially_copyable_v<ipc::RuntimeStatus>);
    STATIC_REQUIRE(std::is_standard_layout_v<ipc::RuntimeStatus>);
    STATIC_REQUIRE(sizeof(ipc::VersionInfo) == 12);
    STATIC_REQUIRE(sizeof(ipc::CompatibilityInfo) == 16);
    STATIC_REQUIRE(sizeof(ipc::RuntimeStatus) == 32);
    STATIC_REQUIRE(ipc::kControlApiMinor == 1);
}

TEST_CASE("major API mismatch is rejected without mutation", "[ipc]") {
    REQUIRE(ipc::NegotiateControlApi(1) == ipc::ApiNegotiationResult::Compatible);
    REQUIRE(ipc::NegotiateControlApi(2) == ipc::ApiNegotiationResult::MajorMismatch);
}

TEST_CASE("recent log count is clamped to phase0 maximum", "[ipc]") {
    REQUIRE(ipc::ClampRecentLogCount(0) == 0);
    REQUIRE(ipc::ClampRecentLogCount(128) == 128);
    REQUIRE(ipc::ClampRecentLogCount(9999) == 128);
}

TEST_CASE("runtime status snapshot reads portable counters", "[ipc]") {
    socket::SocketRegistry registry;
    diagnostics::RingLogger logger;
    REQUIRE(registry.RegisterClient(7));
    REQUIRE(registry.RegisterClient(8));
    registry.UnregisterClient(8);
    REQUIRE(registry.OnSocketCreated(7, 3));
    logger.Push(diagnostics::LogLevel::Warning, "sanitized");

    const auto status = status::BuildRuntimeStatus(
        ipc::RuntimeMode::DisconnectedPassthrough, false, registry, logger, -17);
    REQUIRE(status.active_clients == 1);
    REQUIRE(status.client_high_water == 2);
    REQUIRE(status.active_sockets == 1);
    REQUIRE(status.socket_high_water == 1);
    REQUIRE(status.disable_flag_present == 0);
    REQUIRE(status.last_internal_error == -17);
}
