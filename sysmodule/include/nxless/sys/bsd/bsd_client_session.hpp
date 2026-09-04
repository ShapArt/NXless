#pragma once
#include <cstdint>
#include <span>
#include <nxless/socket/socket_registry.hpp>
#include <nxless/sys/bsd/bsd_forwarder.hpp>
namespace nxless::sys::bsd {
class BsdClientSession {
public:
    BsdClientSession(socket::ClientContextId id, BsdForwarder& forwarder, socket::SocketRegistry& registry) noexcept;
    ~BsdClientSession();
    BsdClientSession(const BsdClientSession&)=delete; BsdClientSession& operator=(const BsdClientSession&)=delete;
    socket::BsdResult Socket(int domain,int type,int protocol) noexcept;
    socket::BsdResult SocketExempt(int domain,int type,int protocol) noexcept;
    socket::BsdResult Accept(int fd,std::span<std::byte> address,std::uint32_t& out_addrlen) noexcept;
    socket::BsdResult Close(int fd) noexcept;
    socket::ClientContextId ContextId() const noexcept { return id_; }
    bool RegistryAttached() const noexcept { return attached_; }
    bool RawPassthroughOnly() const noexcept { return !attached_; }
#if defined(NXLESS_ENABLE_PHASE0_TEST_HOOKS)
    bool MarkProxyCandidateForTest(int fd) noexcept { return registry_.SetTag(id_,fd,socket::InterceptionTag::ProxyCandidate); }
#endif
private:
    socket::ClientContextId id_{}; BsdForwarder& forwarder_; socket::SocketRegistry& registry_; bool attached_{};
};
}
