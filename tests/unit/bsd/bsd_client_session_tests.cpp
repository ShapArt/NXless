#include <array>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <limits>

#include <catch2/catch_test_macros.hpp>

#include <nxless/socket/client_context_id_allocator.hpp>
#include <nxless/sys/bsd/bsd_client_session.hpp>
#include <nxless/sys/bsd/bsd_mitm_server.hpp>

namespace {
class Transport final : public nxless::sys::bsd::IOriginalBsdTransport {
public:
    int next_fd{10};
    int close_errno{};
    std::uint32_t platform_result{};

    std::uint32_t Dispatch(const nxless::sys::bsd::IpcDispatch& request) noexcept override {
        if (platform_result != 0) {
            return platform_result;
        }
        if (request.command_id == 12) {
            struct Output {
                int ret;
                int err;
                std::uint32_t len;
            } output{next_fd++, 0, 16};
            std::memcpy(request.output.data(), &output, sizeof(output));
        } else {
            struct Output {
                int ret;
                int err;
            } output{
                request.command_id == 26 ? (close_errno != 0 ? -1 : 0) : next_fd++,
                request.command_id == 26 ? close_errno : 0,
            };
            std::memcpy(request.output.data(), &output, sizeof(output));
        }
        return 0;
    }
};
} // namespace

TEST_CASE("context allocator never wraps into a live id", "[bsd_session]") {
    nxless::socket::ClientContextIdAllocator allocator(std::numeric_limits<std::uint64_t>::max() - 1);
    const auto first = allocator.Allocate();
    const auto second = allocator.Allocate();
    const auto exhausted = allocator.Allocate();
    REQUIRE(first);
    REQUIRE(second);
    REQUIRE(*first != *second);
    REQUIRE_FALSE(exhausted);
}

TEST_CASE("session with exhausted context is explicitly raw passthrough only", "[bsd_session]") {
    nxless::socket::SocketRegistry registry;
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);
    nxless::sys::bsd::BsdClientSession session(0, forwarder, registry);
    REQUIRE_FALSE(session.RegistryAttached());
    REQUIRE(session.RawPassthroughOnly());
    REQUIRE(registry.ActiveClientCount() == 0);
}

TEST_CASE("session owns socket accept close and teardown registry state", "[bsd_session]") {
    nxless::socket::SocketRegistry registry;
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);
    {
        nxless::sys::bsd::BsdClientSession session(77, forwarder, registry);
        REQUIRE(session.RegistryAttached());

        const auto socket_result = session.Socket(2, 1, 6);
        REQUIRE(socket_result.platform_result == 0);
        REQUIRE(socket_result.bsd.ret == 10);
        REQUIRE(registry.Find(77, 10));

        std::array<std::byte, 32> address{};
        std::uint32_t length = 0;
        const auto accept_result = session.Accept(10, address, length);
        REQUIRE(accept_result.platform_result == 0);
        REQUIRE(accept_result.bsd.ret == 11);
        REQUIRE(registry.Find(77, 11));

        transport.close_errno = EBADF;
        const auto close_result = session.Close(10);
        REQUIRE(close_result.platform_result == 0);
        REQUIRE(close_result.bsd.bsd_errno == EBADF);
        REQUIRE_FALSE(registry.Find(77, 10));
        REQUIRE(registry.ActiveClientCount() == 1);
    }
    REQUIRE(registry.ActiveClientCount() == 0);
    REQUIRE(registry.ActiveSocketCount() == 0);
}

TEST_CASE("duplicate socket is tracked and inherits source interception tag", "[bsd_session]") {
    nxless::socket::SocketRegistry registry;
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);
    nxless::sys::bsd::BsdClientSession session(78, forwarder, registry);

    const auto socket_result = session.Socket(2, 1, 6);
    REQUIRE(socket_result.platform_result == 0);
    REQUIRE(socket_result.bsd.ret == 10);
    REQUIRE(registry.SetTag(78, 10, nxless::socket::InterceptionTag::ProxyCandidate));

    const auto duplicate_result = session.DuplicateSocket(10);
    REQUIRE(duplicate_result.platform_result == 0);
    REQUIRE(duplicate_result.bsd.ret == 11);
    REQUIRE(registry.ActiveSocketCount() == 2);
    const auto duplicate_state = registry.Find(78, 11);
    REQUIRE(duplicate_state);
    REQUIRE(duplicate_state->tag == nxless::socket::InterceptionTag::ProxyCandidate);
}

TEST_CASE("platform failure does not mutate session registry state", "[bsd_session]") {
    nxless::socket::SocketRegistry registry;
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);
    nxless::sys::bsd::BsdClientSession session(91, forwarder, registry);

    const auto created = session.Socket(2, 1, 6);
    REQUIRE(created.platform_result == 0);
    REQUIRE(created.bsd.ret == 10);
    REQUIRE(registry.Find(91, 10));

    const auto socket_count = registry.ActiveSocketCount();
    transport.platform_result = 0x4321U;

    const auto failed_socket = session.Socket(2, 1, 6);
    REQUIRE(failed_socket.platform_result == 0x4321U);
    REQUIRE(registry.ActiveSocketCount() == socket_count);

    const auto failed_close = session.Close(10);
    REQUIRE(failed_close.platform_result == 0x4321U);
    REQUIRE(registry.Find(91, 10));
}

#if defined(NXLESS_ENABLE_PHASE0_TEST_HOOKS)
TEST_CASE("development proxy candidate marker changes only registry tag", "[bsd_session]") {
    nxless::socket::SocketRegistry registry;
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);
    nxless::sys::bsd::BsdClientSession session(88, forwarder, registry);
    const auto result = session.Socket(2, 1, 6);
    REQUIRE(result.platform_result == 0);
    REQUIRE(result.bsd.ret >= 0);
    REQUIRE(session.MarkProxyCandidateForTest(static_cast<int>(result.bsd.ret)));
    REQUIRE(registry.Find(88, static_cast<int>(result.bsd.ret))->tag == nxless::socket::InterceptionTag::ProxyCandidate);
}
#endif

TEST_CASE("mitm admission follows safe boot decision", "[bsd_session]") {
    nxless::sys::bsd::BsdMitmServer::SetAdmissionEnabled(false);
    REQUIRE_FALSE(nxless::sys::bsd::BsdMitmServer::AdmissionEnabled());
    nxless::sys::bsd::BsdMitmServer::SetAdmissionEnabled(true);
    REQUIRE(nxless::sys::bsd::BsdMitmServer::AdmissionEnabled());
    nxless::sys::bsd::BsdMitmServer::SetAdmissionEnabled(false);
}
