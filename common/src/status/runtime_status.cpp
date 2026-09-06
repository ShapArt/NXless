#include <nxless/status/runtime_status.hpp>

#include <limits>

namespace nxless::status {
namespace {

std::uint16_t ToU16(const std::size_t value) noexcept {
    const auto max = static_cast<std::size_t>(std::numeric_limits<std::uint16_t>::max());
    return value > max ? std::numeric_limits<std::uint16_t>::max() : static_cast<std::uint16_t>(value);
}

std::uint32_t ToU32(const std::size_t value) noexcept {
    const auto max = static_cast<std::size_t>(std::numeric_limits<std::uint32_t>::max());
    return value > max ? std::numeric_limits<std::uint32_t>::max() : static_cast<std::uint32_t>(value);
}

} // namespace

ipc::RuntimeStatus BuildRuntimeStatus(const ipc::RuntimeMode mode,
                                      const bool disable_flag_present,
                                      const socket::SocketRegistry& registry,
                                      const diagnostics::RingLogger& logger,
                                      const std::int32_t last_internal_error) noexcept {
    ipc::RuntimeStatus result{};
    result.mode = mode;
    result.disable_flag_present = disable_flag_present ? std::uint8_t{1} : std::uint8_t{0};
    result.client_high_water = ToU16(registry.ClientHighWaterMark());
    result.active_clients = ToU32(registry.ActiveClientCount());
    result.active_sockets = ToU32(registry.ActiveSocketCount());
    result.socket_high_water = ToU32(registry.HighWaterMark());
    result.log_dropped = logger.DroppedCount();
    result.last_internal_error = last_internal_error;
    return result;
}

} // namespace nxless::status
