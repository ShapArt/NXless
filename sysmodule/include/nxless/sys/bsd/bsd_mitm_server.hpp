#pragma once
#include <atomic>
#include <nxless/socket/client_context_id_allocator.hpp>
#include <nxless/socket/socket_registry.hpp>
namespace nxless::sys::bsd {
class BsdMitmService;
inline constexpr std::uint64_t kNxlessProgramId=0x0100000000004E58ULL;
socket::SocketRegistry& GetSharedSocketRegistry() noexcept;
socket::ClientContextIdAllocator& GetClientContextIdAllocator() noexcept;
class BsdMitmServer {
public:
    static void SetAdmissionEnabled(bool enabled) noexcept;
    static bool AdmissionEnabled() noexcept;
};
}
#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere.hpp>
namespace nxless::sys::bsd {
struct BsdMitmManagerOptions {
    static constexpr std::size_t PointerBufferSize=0x1000;
    static constexpr std::size_t MaxDomains=0;
    static constexpr std::size_t MaxDomainObjects=0;
    static constexpr bool CanDeferInvokeRequest=false;
    static constexpr bool CanManageMitmServers=true;
};
class HorizonBsdMitmServer final : public ams::sf::hipc::ServerManager<1,BsdMitmManagerOptions,15> {
public:
    ams::Result RegisterIfAllowed(bool allowed) noexcept;
private:
    ams::Result OnNeedsToAccept(int port_index,Server* server) override;
};
}
#endif
