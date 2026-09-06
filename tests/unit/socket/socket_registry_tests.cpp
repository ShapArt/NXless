#include <catch2/catch_test_macros.hpp>
#include <nxless/socket/socket_registry.hpp>

using namespace nxless::socket;

TEST_CASE("same fd in different clients has independent state", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(1));
    REQUIRE(registry.RegisterClient(2));
    const auto a = registry.OnSocketCreated(1, 7);
    const auto b = registry.OnSocketCreated(2, 7);
    REQUIRE(a.has_value());
    REQUIRE(b.has_value());
    REQUIRE(a->client != b->client);
}

TEST_CASE("fd reuse creates a new generation", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(3));
    const auto first = registry.OnSocketCreated(3, 11);
    REQUIRE(first.has_value());
    REQUIRE(registry.OnSocketClosed(3, 11));
    const auto second = registry.OnSocketCreated(3, 11);
    REQUIRE(second.has_value());
    REQUIRE(second->generation > first->generation);
}

TEST_CASE("unregister client removes only that client sockets", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(10));
    REQUIRE(registry.RegisterClient(20));
    REQUIRE(registry.OnSocketCreated(10, 1));
    REQUIRE(registry.OnSocketCreated(10, 2));
    REQUIRE(registry.OnSocketCreated(20, 1));
    registry.UnregisterClient(10);
    REQUIRE_FALSE(registry.Find(10, 1));
    REQUIRE_FALSE(registry.Find(10, 2));
    REQUIRE(registry.Find(20, 1));
    REQUIRE(registry.ActiveSocketCount() == 1);
}

TEST_CASE("registry capacity is bounded at 512 active sockets", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(42));
    for (int fd = 0; fd < static_cast<int>(SocketRegistry::kMaxSockets); ++fd) {
        REQUIRE(registry.OnSocketCreated(42, fd));
    }
    REQUIRE_FALSE(registry.OnSocketCreated(42, 9999));
    REQUIRE(registry.ActiveSocketCount() == SocketRegistry::kMaxSockets);
    REQUIRE(registry.HighWaterMark() == SocketRegistry::kMaxSockets);
}

TEST_CASE("close is idempotence safe", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(77));
    REQUIRE(registry.OnSocketCreated(77, 8));
    REQUIRE(registry.OnSocketClosed(77, 8));
    REQUIRE_FALSE(registry.OnSocketClosed(77, 8));
    REQUIRE(registry.ActiveSocketCount() == 0);
}

TEST_CASE("socket tags are isolated by client and fd", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE(registry.RegisterClient(1));
    REQUIRE(registry.RegisterClient(2));
    REQUIRE(registry.OnSocketCreated(1, 5));
    REQUIRE(registry.OnSocketCreated(2, 5));
    REQUIRE(registry.SetTag(1, 5, InterceptionTag::ProxyCandidate));
    REQUIRE(registry.Find(1, 5)->tag == InterceptionTag::ProxyCandidate);
    REQUIRE(registry.Find(2, 5)->tag == InterceptionTag::Transparent);
}

TEST_CASE("client high-water survives session churn", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE(registry.ClientHighWaterMark() == 0);
    REQUIRE(registry.RegisterClient(100));
    REQUIRE(registry.RegisterClient(200));
    REQUIRE(registry.ClientHighWaterMark() == 2);

    registry.UnregisterClient(100);
    registry.UnregisterClient(200);
    REQUIRE(registry.ActiveClientCount() == 0);
    REQUIRE(registry.ClientHighWaterMark() == 2);

    REQUIRE(registry.RegisterClient(300));
    REQUIRE(registry.ClientHighWaterMark() == 2);
}

TEST_CASE("client context zero is reserved for passthrough and cannot enter registry", "[socket_registry]") {
    SocketRegistry registry;
    REQUIRE_FALSE(registry.RegisterClient(0));
    REQUIRE(registry.ActiveClientCount() == 0);
    REQUIRE_FALSE(registry.OnSocketCreated(0, 5));
}
