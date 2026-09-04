#include <nxless/ipc/control_runtime.hpp>
#include <algorithm>
#include <nxless/status/runtime_status.hpp>
namespace nxless::ipc {
VersionInfo ControlRuntime::GetVersion() const noexcept { return {kControlApiMajor,kControlApiMinor,0x00000100U}; }
CompatibilityInfo ControlRuntime::GetCompatibility(const std::uint32_t major, const std::uint32_t minor, const std::uint32_t patch, const bool supported) const noexcept {
    return {major,minor,patch,static_cast<std::uint8_t>(supported?1:0),{}};
}
RuntimeStatus ControlRuntime::GetStatus(RuntimeMode mode,bool flag,std::int32_t err) const noexcept {
    return status::BuildRuntimeStatus(mode,flag,registry_,logger_,err);
}
std::size_t ControlRuntime::GetRecentLogs(std::span<ControlLogEventWire> output) const noexcept {
    const std::size_t count=std::min<std::size_t>(output.size(),kMaxRecentLogEvents);
    std::scoped_lock lock(scratch_mutex_);
    const std::size_t written=logger_.SnapshotInto(std::span<diagnostics::LogEvent>(scratch_.data(),count));
    for(std::size_t i=0;i<written;++i){ output[i]={}; output[i].sequence=scratch_[i].sequence; output[i].level=static_cast<std::uint8_t>(scratch_[i].level); output[i].message=scratch_[i].message; }
    return written;
}
}
