#pragma once
#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere.hpp>
#include <nxless/sys/bsd/bsd_client_session.hpp>
#include <nxless/sys/bsd/bsd_mitm_server.hpp>
#include <nxless/sys/bsd/hos_22_5_0/bsd_ipc_adapter.hpp>
namespace nxless::sys::bsd {
class BsdMitmService : public ams::sf::MitmServiceImplBase {
public:
    BsdMitmService(std::shared_ptr<::Service>&& forward,const ams::sm::MitmProcessInfo& client);
    static bool ShouldMitm(const ams::sm::MitmProcessInfo& client) noexcept;
    ams::Result Socket(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,s32 domain,s32 type,s32 protocol) noexcept;
    ams::Result SocketExempt(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,s32 domain,s32 type,s32 protocol) noexcept;
    ams::Result Accept(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,ams::sf::Out<u32> out_addrlen,s32 fd,ams::sf::OutAutoSelectBuffer addr) noexcept;
    ams::Result Close(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,s32 fd) noexcept;
private:
    hos_22_5_0::HorizonOriginalBsdTransport transport_; BsdForwarder forwarder_; BsdClientSession session_;
};
}
#define AMS_NXLESS_BSD_MITM_INTERFACE(C,H) \
 AMS_SF_METHOD_INFO(C,H,2,ams::Result,Socket,(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,s32 domain,s32 type,s32 protocol),(out_ret,out_errno,domain,type,protocol)) \
 AMS_SF_METHOD_INFO(C,H,3,ams::Result,SocketExempt,(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,s32 domain,s32 type,s32 protocol),(out_ret,out_errno,domain,type,protocol)) \
 AMS_SF_METHOD_INFO(C,H,12,ams::Result,Accept,(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,ams::sf::Out<u32> out_addrlen,s32 fd,ams::sf::OutAutoSelectBuffer addr),(out_ret,out_errno,out_addrlen,fd,addr)) \
 AMS_SF_METHOD_INFO(C,H,26,ams::Result,Close,(ams::sf::Out<s32> out_ret,ams::sf::Out<s32> out_errno,s32 fd),(out_ret,out_errno,fd))
AMS_SF_DEFINE_MITM_INTERFACE(nxless::sys::bsd, IBsdMitmService, AMS_NXLESS_BSD_MITM_INTERFACE, 0x4E584C42)
static_assert(nxless::sys::bsd::IsIBsdMitmService<nxless::sys::bsd::BsdMitmService>);
#endif
