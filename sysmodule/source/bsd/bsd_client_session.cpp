#include <nxless/sys/bsd/bsd_client_session.hpp>

namespace nxless::sys::bsd {

BsdClientSession::BsdClientSession(
    const socket::ClientContextId id,
    BsdForwarder& forwarder,
    socket::SocketRegistry& registry) noexcept
    : id_(id),
      forwarder_(forwarder),
      registry_(registry),
      attached_(id != 0 && registry_.RegisterClient(id)) {}

BsdClientSession::~BsdClientSession() {
    if (attached_) {
        registry_.UnregisterClient(id_);
    }
}

BsdForwardResult BsdClientSession::Socket(const int domain, const int type, const int protocol) noexcept {
    const auto result = forwarder_.Socket(domain, type, protocol);
    if (attached_ && result.PlatformSucceeded() && result.bsd.ret >= 0) {
        static_cast<void>(registry_.OnSocketCreated(id_, static_cast<int>(result.bsd.ret)));
    }
    return result;
}

BsdForwardResult BsdClientSession::SocketExempt(
    const int domain,
    const int type,
    const int protocol) noexcept {
    const auto result = forwarder_.SocketExempt(domain, type, protocol);
    if (attached_ && result.PlatformSucceeded() && result.bsd.ret >= 0) {
        static_cast<void>(registry_.OnSocketCreated(id_, static_cast<int>(result.bsd.ret)));
    }
    return result;
}

BsdForwardResult BsdClientSession::Accept(
    const int fd,
    const std::span<std::byte> address,
    std::uint32_t& out_addrlen) noexcept {
    const auto result = forwarder_.Accept(fd, address, out_addrlen);
    if (attached_ && result.PlatformSucceeded() && result.bsd.ret >= 0) {
        static_cast<void>(registry_.OnSocketCreated(id_, static_cast<int>(result.bsd.ret)));
    }
    return result;
}

BsdForwardResult BsdClientSession::Close(const int fd) noexcept {
    const auto result = forwarder_.Close(fd);
    if (attached_ && result.PlatformSucceeded()) {
        static_cast<void>(registry_.OnSocketClosed(id_, fd));
    }
    return result;
}

BsdForwardResult BsdClientSession::DuplicateSocket(const int fd) noexcept {
    const auto source = attached_ ? registry_.Find(id_, fd) : std::nullopt;
    const auto result = forwarder_.DuplicateSocket(fd);
    if (attached_ && result.PlatformSucceeded() && result.bsd.ret >= 0) {
        const int duplicate_fd = static_cast<int>(result.bsd.ret);
        if (registry_.OnSocketCreated(id_, duplicate_fd) && source) {
            static_cast<void>(registry_.SetTag(id_, duplicate_fd, source->tag));
        }
    }
    return result;
}

} // namespace nxless::sys::bsd
