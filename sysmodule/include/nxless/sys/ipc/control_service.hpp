#pragma once
#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere.hpp>
#include <nxless/ipc/control_runtime.hpp>
#include <nxless/ipc/control_state.hpp>

namespace nxless::sys::ipc {
namespace hos = ::ams::hos;
inline constexpr const char* kControlServiceName="nxl:ctl";
class ControlService {
public:
    ControlService(nxless::ipc::ControlRuntime& runtime,
                   nxless::ipc::ControlState& state,
                   bool disable_flag,
                   platform::HosVersion hos) noexcept
        : runtime_(runtime), state_(state), disable_flag_(disable_flag), hos_(hos) {}
    ams::Result GetVersion(ams::sf::Out<nxless::ipc::VersionInfo> out) noexcept;
    ams::Result GetCompatibility(ams::sf::Out<nxless::ipc::CompatibilityInfo> out) noexcept;
    ams::Result GetStatus(ams::sf::Out<nxless::ipc::RuntimeStatus> out) noexcept;
    ams::Result GetRecentLogs(ams::sf::Out<std::uint32_t> out_count, const ams::sf::OutArray<nxless::ipc::ControlLogEventWire>& out) noexcept;
private:
    nxless::ipc::ControlRuntime& runtime_;
    nxless::ipc::ControlState& state_;
    bool disable_flag_;
    platform::HosVersion hos_;
};
}
#define AMS_NXLESS_CTL_INTERFACE(C,H) \
 AMS_SF_METHOD_INFO(C,H,0,ams::Result,GetVersion,(ams::sf::Out<nxless::ipc::VersionInfo> out),(out)) \
 AMS_SF_METHOD_INFO(C,H,1,ams::Result,GetCompatibility,(ams::sf::Out<nxless::ipc::CompatibilityInfo> out),(out)) \
 AMS_SF_METHOD_INFO(C,H,2,ams::Result,GetStatus,(ams::sf::Out<nxless::ipc::RuntimeStatus> out),(out)) \
 AMS_SF_METHOD_INFO(C,H,3,ams::Result,GetRecentLogs,(ams::sf::Out<std::uint32_t> out_count,const ams::sf::OutArray<nxless::ipc::ControlLogEventWire>& out),(out_count,out))
AMS_SF_DEFINE_INTERFACE(nxless::sys::ipc, IControlService, AMS_NXLESS_CTL_INTERFACE, 0x4E584C43)
static_assert(nxless::sys::ipc::IsIControlService<nxless::sys::ipc::ControlService>);
#endif
