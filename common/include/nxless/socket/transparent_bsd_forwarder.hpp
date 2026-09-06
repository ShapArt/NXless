#pragma once

#include <nxless/socket/bsd_backend.hpp>
#include <nxless/socket/socket_registry.hpp>

namespace nxless::socket {

class TransparentBsdForwarder {
public:
    TransparentBsdForwarder(ClientContextId client, IBsdBackend& backend, SocketRegistry& registry) noexcept
        : client_(client), backend_(backend), registry_(registry) {}

    BsdResult Socket(int domain, int type, int protocol) noexcept;
    BsdResult Connect(int fd, ConstBuffer address) noexcept;
    BsdResult Bind(int fd, ConstBuffer address) noexcept { return backend_.Bind(fd, address); }
    BsdResult Listen(int fd, int backlog) noexcept { return backend_.Listen(fd, backlog); }
    BsdResult Accept(int fd, MutableBuffer address) noexcept;
    BsdResult Send(int fd, ConstBuffer data, int flags) noexcept { return backend_.Send(fd, data, flags); }
    BsdResult SendTo(int fd, ConstBuffer data, int flags, ConstBuffer address) noexcept { return backend_.SendTo(fd, data, flags, address); }
    BsdResult Recv(int fd, MutableBuffer data, int flags) noexcept { return backend_.Recv(fd, data, flags); }
    BsdResult RecvFrom(int fd, MutableBuffer data, int flags, MutableBuffer address) noexcept { return backend_.RecvFrom(fd, data, flags, address); }
    BsdResult Read(int fd, MutableBuffer data) noexcept { return backend_.Read(fd, data); }
    BsdResult Write(int fd, ConstBuffer data) noexcept { return backend_.Write(fd, data); }
    BsdResult Poll(MutableBuffer pollfds, std::size_t nfds, int timeout_ms) noexcept { return backend_.Poll(pollfds, nfds, timeout_ms); }
    BsdResult Select(int nfds, MutableBuffer readfds, MutableBuffer writefds, MutableBuffer exceptfds, MutableBuffer timeout) noexcept {
        return backend_.Select(nfds, readfds, writefds, exceptfds, timeout);
    }
    BsdResult Shutdown(int fd, int how) noexcept { return backend_.Shutdown(fd, how); }
    BsdResult GetSockName(int fd, MutableBuffer address) noexcept { return backend_.GetSockName(fd, address); }
    BsdResult GetPeerName(int fd, MutableBuffer address) noexcept { return backend_.GetPeerName(fd, address); }
    BsdResult GetSockOpt(int fd, int level, int optname, MutableBuffer value) noexcept { return backend_.GetSockOpt(fd, level, optname, value); }
    BsdResult SetSockOpt(int fd, int level, int optname, ConstBuffer value) noexcept { return backend_.SetSockOpt(fd, level, optname, value); }
    BsdResult Fcntl(int fd, int command, int argument) noexcept { return backend_.Fcntl(fd, command, argument); }
    BsdResult Ioctl(int fd, std::uint32_t request, MutableBuffer data) noexcept { return backend_.Ioctl(fd, request, data); }
    BsdResult Close(int fd) noexcept;

private:
    ClientContextId client_{};
    IBsdBackend& backend_;
    SocketRegistry& registry_;
};

} // namespace nxless::socket
