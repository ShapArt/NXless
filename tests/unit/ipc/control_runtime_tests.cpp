#include <array>
#include <catch2/catch_test_macros.hpp>
#include <nxless/ipc/control_runtime.hpp>
TEST_CASE("control command surface is read only and bounded", "[control_runtime]") {
    REQUIRE(nxless::ipc::ValidateControlCommand(0)==nxless::ipc::ControlDispatchResult::Supported);
    REQUIRE(nxless::ipc::ValidateControlCommand(3)==nxless::ipc::ControlDispatchResult::Supported);
    REQUIRE(nxless::ipc::ValidateControlCommand(4)==nxless::ipc::ControlDispatchResult::UnsupportedCommand);
}
TEST_CASE("recent logs are capped at 128 and copied to stable wire format", "[control_runtime]") {
    nxless::socket::SocketRegistry registry; nxless::diagnostics::RingLogger logger;
    for(int i=0;i<140;++i) logger.Push(nxless::diagnostics::LogLevel::Info,"bounded");
    nxless::ipc::ControlRuntime runtime(registry,logger); std::array<nxless::ipc::ControlLogEventWire,140> out{};
    REQUIRE(runtime.GetRecentLogs(out)==128); REQUIRE(out[0].sequence!=0); REQUIRE(out[127].message[0]=='b');
}
