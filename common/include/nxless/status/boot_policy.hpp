#pragma once
#include <cstdint>
#include <nxless/ipc/control_protocol.hpp>

namespace nxless::status {

enum class BootAction : std::uint8_t {
    StartControlOnlySafeDisabled,
    StartControlOnlyUnsupportedHos,
    StartControlOnlyErrorPassthrough,
    StartControlAndBsdPassthrough,
};

struct BootInputs {
    bool disable_flag_probe_ok{true};
    bool disable_flag_present{false};
    bool config_read_ok{true};
    bool config_present{false};
    bool config_valid{true};
    bool hos_supported{false};
    bool control_service_available{true};
};

struct BootDecision {
    BootAction action{BootAction::StartControlOnlyErrorPassthrough};
    ipc::RuntimeMode mode{ipc::RuntimeMode::ErrorPassthrough};
    bool bsd_mitm_allowed{false};
};

BootDecision DecideBoot(const BootInputs& inputs) noexcept;

} // namespace nxless::status
