#include <nxless/sys/bsd/bsd_client_session.hpp>
namespace nxless::sys::bsd {
BsdClientSession::BsdClientSession(socket::ClientContextId id,BsdForwarder& f,socket::SocketRegistry& r) noexcept : id_(id),forwarder_(f),registry_(r),attached_(id!=0 && registry_.RegisterClient(id)) {}
BsdClientSession::~BsdClientSession(){ if(attached_) registry_.UnregisterClient(id_); }
socket::BsdResult BsdClientSession::Socket(int d,int t,int p) noexcept { const auto x=forwarder_.Socket(d,t,p); if(attached_&&x.ret>=0)(void)registry_.OnSocketCreated(id_,static_cast<int>(x.ret)); return x; }
socket::BsdResult BsdClientSession::SocketExempt(int d,int t,int p) noexcept { const auto x=forwarder_.SocketExempt(d,t,p); if(attached_&&x.ret>=0)(void)registry_.OnSocketCreated(id_,static_cast<int>(x.ret)); return x; }
socket::BsdResult BsdClientSession::Accept(int fd,std::span<std::byte> a,std::uint32_t& l) noexcept { const auto x=forwarder_.Accept(fd,a,l); if(attached_&&x.ret>=0)(void)registry_.OnSocketCreated(id_,static_cast<int>(x.ret)); return x; }
socket::BsdResult BsdClientSession::Close(int fd) noexcept { const auto x=forwarder_.Close(fd); if(attached_)(void)registry_.OnSocketClosed(id_,fd); return x; }
}
