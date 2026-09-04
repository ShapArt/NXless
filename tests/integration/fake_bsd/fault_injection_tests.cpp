#include <array>
#include <cerrno>
#include <cstddef>
#include <catch2/catch_test_macros.hpp>

#include <nxless/diagnostics/ring_logger.hpp>
#include <nxless/socket/socket_registry.hpp>
#include <nxless/socket/transparent_bsd_forwarder.hpp>

#include "fake_bsd_backend.hpp"

using nxless::socket::ConstBuffer;
using nxless::socket::SocketRegistry;
using nxless::socket::TransparentBsdForwarder;
using nxless::test::FakeBsdBackend;
using nxless::test::InjectedFailure;

TEST_CASE("scripted socket and close failures are deterministic", "[fault_injection]") {
    FakeBsdBackend backend;
    backend.InjectFailure(InjectedFailure::SocketFail);
    const auto socket_result = backend.Socket(2, 1, 6);
    REQUIRE(socket_result.ret == -1);
    REQUIRE(socket_result.bsd_errno == EMFILE);

    backend.InjectFailure(InjectedFailure::CloseFail);
    const auto close_result = backend.Close(5);
    REQUIRE(close_result.ret == -1);
    REQUIRE(close_result.bsd_errno == EBADF);
}

TEST_CASE("ten thousand connect failures do not leak socket state", "[fault_injection]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(9001));

    FakeBsdBackend backend;
    TransparentBsdForwarder forwarder(9001, backend, registry);

    constexpr int kLiveDescriptors = 16;
    for (int fd = 0; fd < kLiveDescriptors; ++fd) {
        REQUIRE(registry.OnSocketCreated(9001, fd));
    }

    backend.InjectFailure(InjectedFailure::ConnectFail);
    std::array<std::byte, 16> address{};
    for (int i = 0; i < 10'000; ++i) {
        const int fd = i % kLiveDescriptors;
        const auto result = forwarder.Connect(fd, ConstBuffer{address});
        REQUIRE(result.ret == -1);
        REQUIRE(result.bsd_errno == ECONNREFUSED);
    }

    REQUIRE(registry.ActiveSocketCount() == static_cast<std::size_t>(kLiveDescriptors));
    REQUIRE(registry.ClientSocketCount(9001) == static_cast<std::size_t>(kLiveDescriptors));

    backend.InjectFailure(InjectedFailure::None);
    backend.SetNext({0, 0});
    for (int fd = 0; fd < kLiveDescriptors; ++fd) {
        REQUIRE(forwarder.Close(fd).ret == 0);
    }
    REQUIRE(registry.ActiveSocketCount() == 0);

    registry.UnregisterClient(9001);
    REQUIRE(registry.ActiveClientCount() == 0);
}

TEST_CASE("backend disappearance returns an error and preserves ownership until close", "[fault_injection]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(9002));
    REQUIRE(registry.OnSocketCreated(9002, 7));

    FakeBsdBackend backend;
    TransparentBsdForwarder forwarder(9002, backend, registry);
    backend.InjectFailure(InjectedFailure::BackendUnavailable);

    std::array<std::byte, 8> payload{};
    const auto result = forwarder.Send(7, ConstBuffer{payload}, 0);
    REQUIRE(result.ret == -1);
    REQUIRE(result.bsd_errno == ENETDOWN);
    REQUIRE(registry.Find(9002, 7));

    const auto close_result = forwarder.Close(7);
    REQUIRE(close_result.ret == -1);
    REQUIRE(close_result.bsd_errno == ENETDOWN);
    REQUIRE_FALSE(registry.Find(9002, 7));
}

TEST_CASE("sleep wake boundary does not invent socket lifecycle transitions", "[fault_injection]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(9003));
    REQUIRE(registry.OnSocketCreated(9003, 3));
    REQUIRE(registry.OnSocketCreated(9003, 4));

    const auto before3 = registry.Find(9003, 3);
    const auto before4 = registry.Find(9003, 4);
    REQUIRE(before3);
    REQUIRE(before4);

    FakeBsdBackend backend;
    backend.SimulateSleepWakeBoundary();
    REQUIRE(backend.LifecycleEpoch() == 1);

    const auto after3 = registry.Find(9003, 3);
    const auto after4 = registry.Find(9003, 4);
    REQUIRE(after3);
    REQUIRE(after4);
    REQUIRE(after3->key.generation == before3->key.generation);
    REQUIRE(after4->key.generation == before4->key.generation);
    REQUIRE(registry.ActiveSocketCount() == 2);
}

TEST_CASE("optional diagnostics allocation denial cannot disable forwarding", "[fault_injection]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(9004));
    REQUIRE(registry.OnSocketCreated(9004, 11));

    nxless::diagnostics::RingLogger logger;
    logger.Push(nxless::diagnostics::LogLevel::Info, "fault-test");
    std::array<nxless::diagnostics::LogEvent, 1> fixed_snapshot{};
    REQUIRE(logger.SnapshotInto(fixed_snapshot) == 1);

    FakeBsdBackend backend;
    backend.InjectFailure(InjectedFailure::AllocationDenied);
    REQUIRE_FALSE(backend.TryOptionalDiagnosticsAllocation());

    backend.SetNext({4, 0});
    TransparentBsdForwarder forwarder(9004, backend, registry);
    std::array<std::byte, 4> payload{};
    const auto result = forwarder.Write(11, ConstBuffer{payload});
    REQUIRE(result.ret == 4);
    REQUIRE(result.bsd_errno == 0);
    REQUIRE(registry.Find(9004, 11));
}
