#include <atomic>
#include <thread>
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

TEST_CASE("control runtime state snapshots never tear mode and error pairs", "[control_runtime]") {
    nxless::ipc::ControlState state;
    state.Store(nxless::ipc::RuntimeMode::DisconnectedPassthrough, 0);

    std::atomic<bool> done{false};
    std::atomic<bool> invalid{false};

    std::thread writer([&] {
        for (int i = 0; i < 200000; ++i) {
            state.Store(nxless::ipc::RuntimeMode::DisconnectedPassthrough, 0);
            state.Store(nxless::ipc::RuntimeMode::ErrorPassthrough, -77);
        }
        done.store(true, std::memory_order_release);
    });

    while (!done.load(std::memory_order_acquire)) {
        const auto snapshot = state.Load();
        const bool valid =
            (snapshot.mode == nxless::ipc::RuntimeMode::DisconnectedPassthrough && snapshot.last_internal_error == 0) ||
            (snapshot.mode == nxless::ipc::RuntimeMode::ErrorPassthrough && snapshot.last_internal_error == -77);
        if (!valid) {
            invalid.store(true, std::memory_order_relaxed);
            break;
        }
    }

    writer.join();
    REQUIRE_FALSE(invalid.load(std::memory_order_relaxed));
}
