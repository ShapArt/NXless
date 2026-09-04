#include <nxless/sys/bsd/bsd_forwarder.hpp>
#include <cstring>
namespace nxless::sys::bsd {
namespace {
struct SocketInput { std::int32_t domain,type,protocol; };
struct RetErrno { std::int32_t ret,bsd_errno; };
struct AcceptOutput { std::int32_t ret,bsd_errno; std::uint32_t addrlen; };
static_assert(sizeof(SocketInput)==12 && sizeof(RetErrno)==8 && sizeof(AcceptOutput)==12);
template<class T> std::span<const std::byte> Bytes(const T& v) noexcept { return {reinterpret_cast<const std::byte*>(&v),sizeof(T)}; }
template<class T> std::span<std::byte> MutableBytes(T& v) noexcept { return {reinterpret_cast<std::byte*>(&v),sizeof(T)}; }
}
socket::BsdResult BsdForwarder::SocketLike(std::uint32_t cmd,int domain,int type,int protocol) noexcept {
    const SocketInput in{domain,type,protocol}; RetErrno out{-1,0}; IpcDispatch req{cmd,Bytes(in),MutableBytes(out),{},0};
    const std::int32_t platform = transport_.Dispatch(req);
    if (platform != 0) {
        return {-1, 0};
    }
    return {out.ret, out.ret < 0 ? out.bsd_errno : 0};
}
socket::BsdResult BsdForwarder::Accept(int fd,std::span<std::byte> address,std::uint32_t& out_addrlen) noexcept {
    if (!FitsHipcU32(address.size())) {
        return {-1, 0};
    }
    const std::int32_t in = fd;
    AcceptOutput out{-1, 0, 0};
    IpcDispatch req{12,Bytes(in),MutableBytes(out),{},1}; req.buffers[0]={address.data(),address.size(),IpcBufferDirection::Out};
    const std::int32_t platform = transport_.Dispatch(req);
    if (platform != 0) {
        return {-1, 0};
    }
    out_addrlen = out.addrlen;
    return {out.ret, out.ret < 0 ? out.bsd_errno : 0};
}
socket::BsdResult BsdForwarder::Close(int fd) noexcept {
    const std::int32_t in=fd; RetErrno out{-1,0}; IpcDispatch req{26,Bytes(in),MutableBytes(out),{},0};
    const std::int32_t platform = transport_.Dispatch(req);
    if (platform != 0) {
        return {-1, 0};
    }
    return {out.ret, out.ret < 0 ? out.bsd_errno : 0};
}
}
