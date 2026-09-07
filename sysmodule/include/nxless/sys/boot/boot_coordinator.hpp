#pragma once
#include <nxless/status/boot_policy.hpp>
#include <nxless/sys/config/sd_config_store.hpp>
#include <nxless/sys/platform/compatibility.hpp>
namespace nxless::sys::boot {
constexpr bool ShouldInstallBsdMitm(const status::BootDecision& decision) noexcept { return decision.bsd_mitm_allowed; }
void ApplyBsdMitmAdmission(const status::BootDecision& decision) noexcept;
status::BootDecision BuildBootDecision(const config::SdLoadResult& sd, platform::HosVersion hos, bool control_service_available) noexcept;
}
