#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <span>

#include <nxless/socket/bsd_backend.hpp>

namespace nxless::sys::bsd {

inline constexpr std::size_t kMaxHipcBuffers = 8;

enum class IpcBufferDirection : std::uint8_t { In, Out, InOut };

struct IpcBuffer {
    void* data{};
    std::size_t size{};
    IpcBufferDirection direction{IpcBufferDirection::In};
};

struct IpcDispatch {
    std::uint32_t command_id{};
    std::span<const std::byte> input{};
    std::span<std::byte> output{};
    std::array<IpcBuffer, kMaxHipcBuffers> buffers{};
    std::size_t buffer_count{};
};

struct BsdForwardResult {
    std::uint32_t platform_result{};
    socket::BsdResult bsd{};

    [[nodiscard]] constexpr bool PlatformSucceeded() const noexcept {
        return platform_result == 0;
    }
};

class IOriginalBsdTransport {
public:
    virtual ~IOriginalBsdTransport() = default;
    virtual std::uint32_t Dispatch(const IpcDispatch& request) noexcept = 0;
};

constexpr bool FitsHipcU32(const std::size_t value) noexcept {
    return value <= static_cast<std::size_t>(std::numeric_limits<std::uint32_t>::max());
}

class BsdForwarder {
public:
    explicit BsdForwarder(IOriginalBsdTransport& transport) noexcept : transport_(transport) {}

    BsdForwardResult Socket(int domain, int type, int protocol) noexcept {
        return SocketLike(2, domain, type, protocol);
    }
    BsdForwardResult SocketExempt(int domain, int type, int protocol) noexcept {
        return SocketLike(3, domain, type, protocol);
    }
    BsdForwardResult Accept(int fd, std::span<std::byte> address, std::uint32_t& out_addrlen) noexcept;
    BsdForwardResult Close(int fd) noexcept;

private:
    BsdForwardResult SocketLike(std::uint32_t command, int domain, int type, int protocol) noexcept;
    IOriginalBsdTransport& transport_;
};

} // namespace nxless::sys::bsd
