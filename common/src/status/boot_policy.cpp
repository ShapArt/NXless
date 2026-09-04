#include <nxless/status/boot_policy.hpp>

namespace nxless::status {
BootDecision DecideBoot(const BootInputs& i) noexcept {
    if (!i.disable_flag_probe_ok) {
        return {BootAction::StartControlOnlyErrorPassthrough, ipc::RuntimeMode::ErrorPassthrough, false};
    }
    if (i.disable_flag_present) {
        return {BootAction::StartControlOnlySafeDisabled, ipc::RuntimeMode::SafeDisabled, false};
    }
    if (!i.hos_supported) {
        return {BootAction::StartControlOnlyUnsupportedHos, ipc::RuntimeMode::UnsupportedHos, false};
    }
    if (!i.config_read_ok || (i.config_present && !i.config_valid) || !i.control_service_available) {
        return {BootAction::StartControlOnlyErrorPassthrough, ipc::RuntimeMode::ErrorPassthrough, false};
    }
    return {BootAction::StartControlAndBsdPassthrough, ipc::RuntimeMode::DisconnectedPassthrough, true};
}
} // namespace nxless::status
