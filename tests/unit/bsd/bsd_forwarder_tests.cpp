#include <array>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <limits>

#include <catch2/catch_test_macros.hpp>

#include <nxless/sys/bsd/bsd_forwarder.hpp>
#include <nxless/sys/bsd/hos_22_5_0/bsd_command_manifest.hpp>

namespace {
class Transport final : public nxless::sys::bsd::IOriginalBsdTransport {
public:
    std::uint32_t last{};
    std::size_t in_size{};
    std::size_t out_size{};
    std::size_t buffer_count{};
    std::int32_t ret{};
    std::int32_t err{};
    std::uint32_t addrlen{16};
    std::uint32_t platform_result{};

    std::uint32_t Dispatch(const nxless::sys::bsd::IpcDispatch& request) noexcept override {
        last = request.command_id;
        in_size = request.input.size();
        out_size = request.output.size();
        buffer_count = request.buffer_count;
        if (platform_result != 0) {
            return platform_result;
        }
        if (request.command_id == 12) {
            struct Output {
                std::int32_t ret;
                std::int32_t err;
                std::uint32_t len;
            } output{ret, err, addrlen};
            std::memcpy(request.output.data(), &output, sizeof(output));
        } else {
            struct Output {
                std::int32_t ret;
                std::int32_t err;
            } output{ret, err};
            std::memcpy(request.output.data(), &output, sizeof(output));
        }
        return 0;
    }
};
} // namespace

TEST_CASE("manifest is complete and hooks only stateful phase0 commands", "[bsd_manifest]") {
    using namespace nxless::sys::bsd::hos_22_5_0;
    REQUIRE(kCommandManifest.size() == 46);
    REQUIRE(HandlingFor(2) == Handling::ForwardWithStateHook);
    REQUIRE(HandlingFor(3) == Handling::ForwardWithStateHook);
    REQUIRE(HandlingFor(12) == Handling::ForwardWithStateHook);
    REQUIRE(HandlingFor(26) == Handling::ForwardWithStateHook);
    REQUIRE(HandlingFor(14) == Handling::RawForward);
    REQUIRE(HandlingFor(43) == Handling::RawForward);
}

TEST_CASE("socket and close use pinned command ids and ret errno layout", "[bsd_forwarder]") {
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);

    transport.ret = -1;
    transport.err = ECONNREFUSED;
    auto result = forwarder.Socket(2, 1, 6);
    REQUIRE(result.platform_result == 0);
    REQUIRE(transport.last == 2);
    REQUIRE(transport.in_size == 12);
    REQUIRE(transport.out_size == 8);
    REQUIRE(result.bsd.ret == -1);
    REQUIRE(result.bsd.bsd_errno == ECONNREFUSED);

    transport.ret = 0;
    transport.err = 99;
    result = forwarder.Close(7);
    REQUIRE(result.platform_result == 0);
    REQUIRE(transport.last == 26);
    REQUIRE(result.bsd.ret == 0);
    REQUIRE(result.bsd.bsd_errno == 0);
}

TEST_CASE("accept preserves 12 byte output including addrlen", "[bsd_forwarder]") {
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);
    std::array<std::byte, 32> address{};
    std::uint32_t length = 0;

    transport.ret = 9;
    transport.addrlen = 16;
    const auto result = forwarder.Accept(3, address, length);
    REQUIRE(result.platform_result == 0);
    REQUIRE(transport.last == 12);
    REQUIRE(transport.out_size == 12);
    REQUIRE(transport.buffer_count == 1);
    REQUIRE(result.bsd.ret == 9);
    REQUIRE(length == 16);
}

TEST_CASE("platform dispatch failure is distinct from BSD ret errno", "[bsd_forwarder]") {
    Transport transport;
    nxless::sys::bsd::BsdForwarder forwarder(transport);
    transport.platform_result = 0x1234U;
    transport.ret = 99;
    transport.err = ECONNRESET;

    const auto result = forwarder.Socket(2, 1, 6);
    REQUIRE(result.platform_result == 0x1234U);
    REQUIRE(result.bsd.ret == -1);
    REQUIRE(result.bsd.bsd_errno == 0);
}

TEST_CASE("hipc u32 size boundary is explicit", "[bsd_forwarder]") {
    using nxless::sys::bsd::FitsHipcU32;
    REQUIRE(FitsHipcU32(std::numeric_limits<std::uint32_t>::max()));
    if constexpr (sizeof(std::size_t) > 4) {
        REQUIRE_FALSE(FitsHipcU32(static_cast<std::size_t>(std::numeric_limits<std::uint32_t>::max()) + 1ULL));
    }
}
