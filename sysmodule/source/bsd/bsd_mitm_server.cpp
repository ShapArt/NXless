#include <nxless/sys/bsd/bsd_mitm_server.hpp>
namespace nxless::sys::bsd {
namespace { socket::SocketRegistry g_registry; socket::ClientContextIdAllocator g_ids; std::atomic<bool> g_admission{false}; }
socket::SocketRegistry& GetSharedSocketRegistry() noexcept { return g_registry; }
socket::ClientContextIdAllocator& GetClientContextIdAllocator() noexcept { return g_ids; }
void BsdMitmServer::SetAdmissionEnabled(bool enabled) noexcept { g_admission.store(enabled,std::memory_order_release); }
bool BsdMitmServer::AdmissionEnabled() noexcept { return g_admission.load(std::memory_order_acquire); }
}
#if defined(ATMOSPHERE_OS_HORIZON)
#include <nxless/sys/bsd/bsd_mitm_service.hpp>
namespace nxless::sys::bsd {
ams::Result HorizonBsdMitmServer::RegisterIfAllowed(const bool allowed) noexcept {
    BsdMitmServer::SetAdmissionEnabled(allowed);
    if (!allowed) { R_SUCCEED(); }
    constexpr ams::sm::ServiceName name=ams::sm::ServiceName::Encode("bsd:u");
    R_RETURN(this->RegisterMitmServer<BsdMitmService>(0,name));
}
ams::Result HorizonBsdMitmServer::OnNeedsToAccept(const int port_index,Server* server) {
    if (port_index != 0) { R_THROW(ams::sf::ResultNotSupported()); }
    std::shared_ptr<::Service> forward;
    ams::sm::MitmProcessInfo client{};
    server->AcknowledgeMitmSession(std::addressof(forward),std::addressof(client));
    auto object=ams::sf::CreateSharedObjectEmplaced<IBsdMitmService,BsdMitmService>(std::shared_ptr<::Service>(forward),client);
    R_RETURN(this->AcceptMitmImpl(server,std::move(object),forward));
}
}
#endif
