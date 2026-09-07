#include <nxless/sys/boot/boot_coordinator.hpp>
#include <nxless/sys/bsd/bsd_mitm_server.hpp>
namespace nxless::sys::boot {
void ApplyBsdMitmAdmission(const status::BootDecision& decision) noexcept {
    bsd::BsdMitmServer::SetAdmissionEnabled(ShouldInstallBsdMitm(decision));
}
status::BootDecision BuildBootDecision(const config::SdLoadResult& sd, platform::HosVersion hos, bool control) noexcept {
    const bool present = sd.config_status != config::SdReadStatus::Missing;
    const bool read_ok = sd.config_status == config::SdReadStatus::Ok || sd.config_status == config::SdReadStatus::Missing;
    const bool valid = !present || !sd.parsed.error.has_value();
    return status::DecideBoot({sd.disable_probe_ok, sd.disable_flag_present, read_ok, present, valid,
                              platform::IsPhase0SupportedHos(hos), control});
}
}
