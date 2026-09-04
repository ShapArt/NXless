#include <nxless/ipc/control_state.hpp>

#include <atomic>
#include <cstdint>
#include <thread>

#include <catch2/catch_test_macros.hpp>

TEST_CASE("control state preserves an atomic mode/error snapshot") {
    nxless::ipc::ControlState state;

    constexpr auto mode_a = nxless::ipc::RuntimeMode::DisconnectedPassthrough;
    constexpr std::int32_t error_a = 0x12345678;
    constexpr auto mode_b = nxless::ipc::RuntimeMode::ErrorPassthrough;
    constexpr std::int32_t error_b = -0x1234567;

    state.Store(mode_a, error_a);
    std::atomic<bool> running{true};
    std::atomic<bool> torn{false};

    std::thread reader([&] {
        while (running.load(std::memory_order_acquire)) {
            const auto snapshot = state.Load();
            const bool pair_a = snapshot.mode == mode_a && snapshot.last_internal_error == error_a;
            const bool pair_b = snapshot.mode == mode_b && snapshot.last_internal_error == error_b;
            if (!pair_a && !pair_b) {
                torn.store(true, std::memory_order_release);
                return;
            }
        }
    });

    for (std::size_t i = 0; i < 200000; ++i) {
        state.Store(mode_b, error_b);
        state.Store(mode_a, error_a);
    }
    running.store(false, std::memory_order_release);
    reader.join();

    REQUIRE_FALSE(torn.load(std::memory_order_acquire));
}

TEST_CASE("control state partial updates preserve the other field") {
    nxless::ipc::ControlState state;
    state.Store(nxless::ipc::RuntimeMode::SafeDisabled, 17);

    state.SetMode(nxless::ipc::RuntimeMode::UnsupportedHos);
    auto snapshot = state.Load();
    REQUIRE(snapshot.mode == nxless::ipc::RuntimeMode::UnsupportedHos);
    REQUIRE(snapshot.last_internal_error == 17);

    state.SetLastInternalError(-42);
    snapshot = state.Load();
    REQUIRE(snapshot.mode == nxless::ipc::RuntimeMode::UnsupportedHos);
    REQUIRE(snapshot.last_internal_error == -42);
}
