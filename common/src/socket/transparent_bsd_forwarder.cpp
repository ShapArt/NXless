#include <nxless/socket/transparent_bsd_forwarder.hpp>

namespace nxless::socket {

BsdResult TransparentBsdForwarder::Socket(const int domain, const int type, const int protocol) noexcept {
    const BsdResult result = backend_.Socket(domain, type, protocol);
    if (result.ret >= 0) {
        (void)registry_.OnSocketCreated(client_, static_cast<int>(result.ret));
    }
    return result;
}

BsdResult TransparentBsdForwarder::Connect(const int fd, const ConstBuffer address) noexcept {
    return backend_.Connect(fd, address);
}

BsdResult TransparentBsdForwarder::Accept(const int fd, const MutableBuffer address) noexcept {
    const BsdResult result = backend_.Accept(fd, address);
    if (result.ret >= 0) {
        (void)registry_.OnSocketCreated(client_, static_cast<int>(result.ret));
    }
    return result;
}

BsdResult TransparentBsdForwarder::Close(const int fd) noexcept {
    const BsdResult result = backend_.Close(fd);
    (void)registry_.OnSocketClosed(client_, fd);
    return result;
}

} // namespace nxless::socket
