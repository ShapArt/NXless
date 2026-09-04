#include <nxless/sys/ipc/control_service.hpp>
#if defined(ATMOSPHERE_OS_HORIZON)
namespace nxless::sys::ipc {
ams::Result ControlService::GetVersion(ams::sf::Out<nxless::ipc::VersionInfo> out) noexcept { *out=runtime_.GetVersion(); R_SUCCEED(); }
ams::Result ControlService::GetCompatibility(ams::sf::Out<nxless::ipc::CompatibilityInfo> out) noexcept { *out=runtime_.GetCompatibility(hos_->major,hos_->minor,hos_->patch,platform::IsPhase0SupportedHos(*hos_)); R_SUCCEED(); }
ams::Result ControlService::GetStatus(ams::sf::Out<nxless::ipc::RuntimeStatus> out) noexcept { *out=runtime_.GetStatus(*mode_,*disable_flag_,*last_error_); R_SUCCEED(); }
ams::Result ControlService::GetRecentLogs(ams::sf::Out<std::uint32_t> out_count,const ams::sf::OutArray<nxless::ipc::ControlLogEventWire>& out) noexcept {
    const std::size_t count=runtime_.GetRecentLogs(std::span<nxless::ipc::ControlLogEventWire>(out.GetPointer(),out.GetSize()));
    *out_count=static_cast<std::uint32_t>(count); R_SUCCEED();
}
}
#endif
