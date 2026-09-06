#include <array>
#include <cerrno>
#include <catch2/catch_test_macros.hpp>
#include <nxless/socket/transparent_bsd_forwarder.hpp>
#include "fake_bsd_backend.hpp"

using namespace nxless::socket;
using nxless::test::BsdCallKind;
using nxless::test::FakeBsdBackend;

TEST_CASE("connect preserves result errno and destination", "[fake_bsd]") {
    SocketRegistry registry; REQUIRE(registry.RegisterClient(1)); REQUIRE(registry.OnSocketCreated(1,7));
    FakeBsdBackend backend; backend.SetNext({-1, ECONNREFUSED});
    TransparentBsdForwarder fwd(1, backend, registry);
    std::array<std::byte,4> address{std::byte{1},std::byte{2},std::byte{3},std::byte{4}};
    const auto result=fwd.Connect(7, ConstBuffer{address});
    REQUIRE(result.ret == -1); REQUIRE(result.bsd_errno == ECONNREFUSED);
    REQUIRE(backend.LastCall().kind == BsdCallKind::Connect); REQUIRE(backend.LastCall().fd == 7);
    REQUIRE(backend.LastCall().bytes_size == address.size());
}

TEST_CASE("socket state is created only after backend succeeds", "[fake_bsd]") {
    SocketRegistry registry; REQUIRE(registry.RegisterClient(2)); FakeBsdBackend backend;
    TransparentBsdForwarder fwd(2,backend,registry);
    backend.SetNext({-1, ENOMEM}); REQUIRE(fwd.Socket(2,1,6).ret < 0); REQUIRE(registry.ActiveSocketCount()==0);
    backend.SetNext({19,0}); REQUIRE(fwd.Socket(2,1,6).ret==19); REQUIRE(registry.Find(2,19));
}

TEST_CASE("close removes registry ownership even when backend close fails", "[fake_bsd]") {
    SocketRegistry registry; REQUIRE(registry.RegisterClient(3)); REQUIRE(registry.OnSocketCreated(3,8)); FakeBsdBackend backend;
    TransparentBsdForwarder fwd(3,backend,registry); backend.SetNext({-1, EBADF});
    REQUIRE(fwd.Close(8).bsd_errno==EBADF); REQUIRE_FALSE(registry.Find(3,8));
    REQUIRE(fwd.Close(8).bsd_errno==EBADF); REQUIRE(registry.ActiveSocketCount()==0);
}

TEST_CASE("proxy candidate is still transparent in phase0", "[fake_bsd]") {
    SocketRegistry registry; REQUIRE(registry.RegisterClient(4)); REQUIRE(registry.OnSocketCreated(4,9)); REQUIRE(registry.SetTag(4,9,InterceptionTag::ProxyCandidate));
    FakeBsdBackend backend; backend.SetNext({0,0}); TransparentBsdForwarder fwd(4,backend,registry);
    std::array<std::byte,3> dst{std::byte{0x10},std::byte{0x20},std::byte{0x30}};
    REQUIRE(fwd.Connect(9,ConstBuffer{dst}).ret==0); REQUIRE(backend.CallCount()==1); REQUIRE(backend.LastCall().bytes_size==dst.size());
}

TEST_CASE("accept creates state for returned fd only on success", "[fake_bsd]") {
    SocketRegistry registry; REQUIRE(registry.RegisterClient(5)); REQUIRE(registry.OnSocketCreated(5,3)); FakeBsdBackend backend; TransparentBsdForwarder fwd(5,backend,registry);
    std::array<std::byte,32> addr{}; backend.SetNext({22,0}); REQUIRE(fwd.Accept(3,MutableBuffer{addr}).ret==22); REQUIRE(registry.Find(5,22));
}
