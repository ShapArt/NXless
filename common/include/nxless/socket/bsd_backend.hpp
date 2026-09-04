#pragma once

#include <cstddef>
#include <cstdint>
#include <span>

namespace nxless::socket {

struct BsdResult {
    std::int64_t ret{-1};
    std::int32_t bsd_errno{0};
};

struct MutableBuffer {
    std::span<std::byte> bytes{};
};
struct ConstBuffer {
    std::span<const std::byte> bytes{};
};

class IBsdBackend {
public:
    virtual ~IBsdBackend() = default;

    virtual BsdResult Socket(int domain, int type, int protocol) noexcept = 0;
    virtual BsdResult Connect(int fd, ConstBuffer address) noexcept = 0;
    virtual BsdResult Bind(int fd, ConstBuffer address) noexcept = 0;
    virtual BsdResult Listen(int fd, int backlog) noexcept = 0;
    virtual BsdResult Accept(int fd, MutableBuffer address) noexcept = 0;
    virtual BsdResult Send(int fd, ConstBuffer data, int flags) noexcept = 0;
    virtual BsdResult SendTo(int fd, ConstBuffer data, int flags, ConstBuffer address) noexcept = 0;
    virtual BsdResult Recv(int fd, MutableBuffer data, int flags) noexcept = 0;
    virtual BsdResult RecvFrom(int fd, MutableBuffer data, int flags, MutableBuffer address) noexcept = 0;
    virtual BsdResult Read(int fd, MutableBuffer data) noexcept = 0;
    virtual BsdResult Write(int fd, ConstBuffer data) noexcept = 0;
    virtual BsdResult Poll(MutableBuffer pollfds, std::size_t nfds, int timeout_ms) noexcept = 0;
    virtual BsdResult Select(int nfds, MutableBuffer readfds, MutableBuffer writefds,
                             MutableBuffer exceptfds, MutableBuffer timeout) noexcept = 0;
    virtual BsdResult Shutdown(int fd, int how) noexcept = 0;
    virtual BsdResult GetSockName(int fd, MutableBuffer address) noexcept = 0;
    virtual BsdResult GetPeerName(int fd, MutableBuffer address) noexcept = 0;
    virtual BsdResult GetSockOpt(int fd, int level, int optname, MutableBuffer value) noexcept = 0;
    virtual BsdResult SetSockOpt(int fd, int level, int optname, ConstBuffer value) noexcept = 0;
    virtual BsdResult Fcntl(int fd, int command, int argument) noexcept = 0;
    virtual BsdResult Ioctl(int fd, std::uint32_t request, MutableBuffer data) noexcept = 0;
    virtual BsdResult Close(int fd) noexcept = 0;
};

} // namespace nxless::socket
