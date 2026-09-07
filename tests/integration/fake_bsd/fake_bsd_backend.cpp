#include "fake_bsd_backend.hpp"

#include <algorithm>
#include <cerrno>

namespace nxless::test {
using namespace nxless::socket;

BsdResult FakeBsdBackend::ResultFor(const BsdCallKind kind) const noexcept {
    if (failure_ == InjectedFailure::BackendUnavailable) {
        return {-1, ENETDOWN};
    }
    if (failure_ == InjectedFailure::SocketFail && kind == BsdCallKind::Socket) {
        return {-1, EMFILE};
    }
    if (failure_ == InjectedFailure::ConnectFail && kind == BsdCallKind::Connect) {
        return {-1, ECONNREFUSED};
    }
    if (failure_ == InjectedFailure::CloseFail && kind == BsdCallKind::Close) {
        return {-1, EBADF};
    }
    return next_;
}

BsdResult FakeBsdBackend::Record(BsdCallKind kind, int fd, int a, int b, ConstBuffer data) noexcept {
    last_ = {};
    last_.kind = kind; last_.fd = fd; last_.a = a; last_.b = b;
    last_.bytes_size = std::min(data.bytes.size(), last_.bytes.size());
    if (last_.bytes_size != 0) std::memcpy(last_.bytes.data(), data.bytes.data(), last_.bytes_size);
    ++call_count_;
    return ResultFor(kind);
}
BsdResult FakeBsdBackend::RecordMutable(BsdCallKind kind, int fd, MutableBuffer data) noexcept {
    return Record(kind, fd, 0, 0, ConstBuffer{std::span<const std::byte>(data.bytes.data(), data.bytes.size())});
}
BsdResult FakeBsdBackend::Socket(int d,int t,int p) noexcept {
    const BsdResult result = Record(BsdCallKind::Socket, -1, d, t, {});
    last_.request = static_cast<std::uint32_t>(p);
    return result;
}
BsdResult FakeBsdBackend::Connect(int fd,ConstBuffer x) noexcept { return Record(BsdCallKind::Connect,fd,0,0,x); }
BsdResult FakeBsdBackend::Bind(int fd,ConstBuffer x) noexcept { return Record(BsdCallKind::Bind,fd,0,0,x); }
BsdResult FakeBsdBackend::Listen(int fd,int b) noexcept { return Record(BsdCallKind::Listen,fd,b); }
BsdResult FakeBsdBackend::Accept(int fd,MutableBuffer x) noexcept { return RecordMutable(BsdCallKind::Accept,fd,x); }
BsdResult FakeBsdBackend::Send(int fd,ConstBuffer x,int f) noexcept { return Record(BsdCallKind::Send,fd,f,0,x); }
BsdResult FakeBsdBackend::SendTo(int fd,ConstBuffer x,int f,ConstBuffer) noexcept { return Record(BsdCallKind::SendTo,fd,f,0,x); }
BsdResult FakeBsdBackend::Recv(int fd,MutableBuffer x,int f) noexcept { return Record(BsdCallKind::Recv,fd,f,0,ConstBuffer{std::span<const std::byte>(x.bytes.data(),x.bytes.size())}); }
BsdResult FakeBsdBackend::RecvFrom(int fd,MutableBuffer x,int f,MutableBuffer) noexcept { return Record(BsdCallKind::RecvFrom,fd,f,0,ConstBuffer{std::span<const std::byte>(x.bytes.data(),x.bytes.size())}); }
BsdResult FakeBsdBackend::Read(int fd,MutableBuffer x) noexcept { return RecordMutable(BsdCallKind::Read,fd,x); }
BsdResult FakeBsdBackend::Write(int fd,ConstBuffer x) noexcept { return Record(BsdCallKind::Write,fd,0,0,x); }
BsdResult FakeBsdBackend::Poll(MutableBuffer x,std::size_t n,int t) noexcept { return Record(BsdCallKind::Poll,-1,static_cast<int>(n),t,ConstBuffer{std::span<const std::byte>(x.bytes.data(),x.bytes.size())}); }
BsdResult FakeBsdBackend::Select(int n,MutableBuffer r,MutableBuffer,MutableBuffer,MutableBuffer) noexcept { return Record(BsdCallKind::Select,-1,n,0,ConstBuffer{std::span<const std::byte>(r.bytes.data(),r.bytes.size())}); }
BsdResult FakeBsdBackend::Shutdown(int fd,int h) noexcept { return Record(BsdCallKind::Shutdown,fd,h); }
BsdResult FakeBsdBackend::GetSockName(int fd,MutableBuffer x) noexcept { return RecordMutable(BsdCallKind::GetSockName,fd,x); }
BsdResult FakeBsdBackend::GetPeerName(int fd,MutableBuffer x) noexcept { return RecordMutable(BsdCallKind::GetPeerName,fd,x); }
BsdResult FakeBsdBackend::GetSockOpt(int fd,int l,int o,MutableBuffer x) noexcept { return Record(BsdCallKind::GetSockOpt,fd,l,o,ConstBuffer{std::span<const std::byte>(x.bytes.data(),x.bytes.size())}); }
BsdResult FakeBsdBackend::SetSockOpt(int fd,int l,int o,ConstBuffer x) noexcept { return Record(BsdCallKind::SetSockOpt,fd,l,o,x); }
BsdResult FakeBsdBackend::Fcntl(int fd,int c,int a) noexcept { return Record(BsdCallKind::Fcntl,fd,c,a); }
BsdResult FakeBsdBackend::Ioctl(int fd,std::uint32_t q,MutableBuffer x) noexcept { last_.request=q; auto r=RecordMutable(BsdCallKind::Ioctl,fd,x); last_.request=q; return r; }
BsdResult FakeBsdBackend::Close(int fd) noexcept { return Record(BsdCallKind::Close,fd); }

} // namespace nxless::test
