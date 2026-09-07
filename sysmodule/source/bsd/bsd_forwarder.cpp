#include <nxless/sys/bsd/bsd_forwarder.hpp>

#include <cerrno>
#include <cstring>

namespace nxless::sys::bsd {
namespace {

struct SocketInput {
    std::int32_t domain;
    std::int32_t type;
    std::int32_t protocol;
};

struct RetErrno {
    std::int32_t ret;
    std::int32_t bsd_errno;
};

struct AcceptOutput {
    std::int32_t ret;
    std::int32_t bsd_errno;
    std::uint32_t addrlen;
};

static_assert(sizeof(SocketInput) == 12);
static_assert(sizeof(RetErrno) == 8);
static_assert(sizeof(AcceptOutput) == 12);

template <class T>
std::span<const std::byte> Bytes(const T& value) noexcept {
    return {reinterpret_cast<const std::byte*>(&value), sizeof(T)};
}

template <class T>
std::span<std::byte> MutableBytes(T& value) noexcept {
    return {reinterpret_cast<std::byte*>(&value), sizeof(T)};
}

} // namespace

BsdForwardResult BsdForwarder::SocketLike(
    const std::uint32_t command,
    const int domain,
    const int type,
    const int protocol) noexcept {
    const SocketInput input{domain, type, protocol};
    RetErrno output{-1, 0};
    IpcDispatch request{command, Bytes(input), MutableBytes(output), {}, 0};

    const std::uint32_t platform_result = transport_.Dispatch(request);
    if (platform_result != 0) {
        return {platform_result, {-1, 0}};
    }

    return {0, {output.ret, output.ret < 0 ? output.bsd_errno : 0}};
}

BsdForwardResult BsdForwarder::Accept(
    const int fd,
    const std::span<std::byte> address,
    std::uint32_t& out_addrlen) noexcept {
    if (!FitsHipcU32(address.size())) {
        return {0, {-1, EINVAL}};
    }

    const std::int32_t input = fd;
    AcceptOutput output{-1, 0, 0};
    IpcDispatch request{12, Bytes(input), MutableBytes(output), {}, 1};
    request.buffers[0] = {address.data(), address.size(), IpcBufferDirection::Out};

    const std::uint32_t platform_result = transport_.Dispatch(request);
    if (platform_result != 0) {
        return {platform_result, {-1, 0}};
    }

    out_addrlen = output.addrlen;
    return {0, {output.ret, output.ret < 0 ? output.bsd_errno : 0}};
}

BsdForwardResult BsdForwarder::Close(const int fd) noexcept {
    const std::int32_t input = fd;
    RetErrno output{-1, 0};
    IpcDispatch request{26, Bytes(input), MutableBytes(output), {}, 0};

    const std::uint32_t platform_result = transport_.Dispatch(request);
    if (platform_result != 0) {
        return {platform_result, {-1, 0}};
    }

    return {0, {output.ret, output.ret < 0 ? output.bsd_errno : 0}};
}

} // namespace nxless::sys::bsd
