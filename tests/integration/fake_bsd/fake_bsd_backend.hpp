#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>

#include <nxless/socket/bsd_backend.hpp>

namespace nxless::test {

enum class BsdCallKind : std::uint8_t {
    Socket, Connect, Bind, Listen, Accept, Send, SendTo, Recv, RecvFrom, Read, Write,
    Poll, Select, Shutdown, GetSockName, GetPeerName, GetSockOpt, SetSockOpt, Fcntl, Ioctl, Close,
};

enum class InjectedFailure : std::uint8_t {
    None,
    SocketFail,
    ConnectFail,
    CloseFail,
    BackendUnavailable,
    AllocationDenied,
};

struct BsdCall {
    BsdCallKind kind{};
    int fd{-1};
    int a{};
    int b{};
    std::uint32_t request{};
    std::array<std::byte, 64> bytes{};
    std::size_t bytes_size{};
};

class FakeBsdBackend final : public nxless::socket::IBsdBackend {
public:
    void SetNext(nxless::socket::BsdResult result) noexcept { next_ = result; }
    void InjectFailure(InjectedFailure failure) noexcept { failure_ = failure; }
    bool TryOptionalDiagnosticsAllocation() const noexcept { return failure_ != InjectedFailure::AllocationDenied; }
    void SimulateSleepWakeBoundary() noexcept { ++lifecycle_epoch_; }
    std::uint64_t LifecycleEpoch() const noexcept { return lifecycle_epoch_; }
    const BsdCall& LastCall() const noexcept { return last_; }
    std::size_t CallCount() const noexcept { return call_count_; }

    nxless::socket::BsdResult Socket(int domain, int type, int protocol) noexcept override;
    nxless::socket::BsdResult Connect(int fd, nxless::socket::ConstBuffer address) noexcept override;
    nxless::socket::BsdResult Bind(int fd, nxless::socket::ConstBuffer address) noexcept override;
    nxless::socket::BsdResult Listen(int fd, int backlog) noexcept override;
    nxless::socket::BsdResult Accept(int fd, nxless::socket::MutableBuffer address) noexcept override;
    nxless::socket::BsdResult Send(int fd, nxless::socket::ConstBuffer data, int flags) noexcept override;
    nxless::socket::BsdResult SendTo(int fd, nxless::socket::ConstBuffer data, int flags, nxless::socket::ConstBuffer address) noexcept override;
    nxless::socket::BsdResult Recv(int fd, nxless::socket::MutableBuffer data, int flags) noexcept override;
    nxless::socket::BsdResult RecvFrom(int fd, nxless::socket::MutableBuffer data, int flags, nxless::socket::MutableBuffer address) noexcept override;
    nxless::socket::BsdResult Read(int fd, nxless::socket::MutableBuffer data) noexcept override;
    nxless::socket::BsdResult Write(int fd, nxless::socket::ConstBuffer data) noexcept override;
    nxless::socket::BsdResult Poll(nxless::socket::MutableBuffer pollfds, std::size_t nfds, int timeout_ms) noexcept override;
    nxless::socket::BsdResult Select(int nfds, nxless::socket::MutableBuffer readfds, nxless::socket::MutableBuffer writefds,
                                     nxless::socket::MutableBuffer exceptfds, nxless::socket::MutableBuffer timeout) noexcept override;
    nxless::socket::BsdResult Shutdown(int fd, int how) noexcept override;
    nxless::socket::BsdResult GetSockName(int fd, nxless::socket::MutableBuffer address) noexcept override;
    nxless::socket::BsdResult GetPeerName(int fd, nxless::socket::MutableBuffer address) noexcept override;
    nxless::socket::BsdResult GetSockOpt(int fd, int level, int optname, nxless::socket::MutableBuffer value) noexcept override;
    nxless::socket::BsdResult SetSockOpt(int fd, int level, int optname, nxless::socket::ConstBuffer value) noexcept override;
    nxless::socket::BsdResult Fcntl(int fd, int command, int argument) noexcept override;
    nxless::socket::BsdResult Ioctl(int fd, std::uint32_t request, nxless::socket::MutableBuffer data) noexcept override;
    nxless::socket::BsdResult Close(int fd) noexcept override;

private:
    nxless::socket::BsdResult Record(BsdCallKind kind, int fd = -1, int a = 0, int b = 0,
                                      nxless::socket::ConstBuffer bytes = {}) noexcept;
    nxless::socket::BsdResult ResultFor(BsdCallKind kind) const noexcept;
    nxless::socket::BsdResult RecordMutable(BsdCallKind kind, int fd, nxless::socket::MutableBuffer bytes) noexcept;

    nxless::socket::BsdResult next_{0, 0};
    InjectedFailure failure_{InjectedFailure::None};
    BsdCall last_{};
    std::size_t call_count_{};
    std::uint64_t lifecycle_epoch_{};
};

} // namespace nxless::test
