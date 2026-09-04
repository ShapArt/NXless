#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <mutex>
#include <type_traits>
#include <nxless/diagnostics/ring_logger.hpp>
#include <nxless/ipc/control_protocol.hpp>
#include <nxless/ipc/control_state.hpp>
#include <nxless/socket/socket_registry.hpp>

namespace nxless::ipc {
enum class ControlCommand : std::uint32_t { GetVersion=0, GetCompatibility=1, GetStatus=2, GetRecentLogs=3 };
enum class ControlDispatchResult : std::uint8_t { Supported, UnsupportedCommand };
constexpr ControlDispatchResult ValidateControlCommand(std::uint32_t id) noexcept { return id<=3U ? ControlDispatchResult::Supported : ControlDispatchResult::UnsupportedCommand; }

struct ControlLogEventWire {
    std::uint64_t sequence{};
    std::uint8_t level{};
    std::array<std::uint8_t,7> reserved{};
    std::array<char,160> message{};
};
static_assert(sizeof(ControlLogEventWire)==176);
static_assert(std::is_trivially_copyable_v<ControlLogEventWire> && std::is_standard_layout_v<ControlLogEventWire>);

class ControlRuntime {
public:
    ControlRuntime(const socket::SocketRegistry& registry, const diagnostics::RingLogger& logger) noexcept : registry_(registry), logger_(logger) {}
    VersionInfo GetVersion() const noexcept;
    CompatibilityInfo GetCompatibility(std::uint32_t hos_major, std::uint32_t hos_minor, std::uint32_t hos_patch, bool bsd_supported) const noexcept;
    RuntimeStatus GetStatus(RuntimeMode mode, bool disable_flag, std::int32_t last_error) const noexcept;
    std::size_t GetRecentLogs(std::span<ControlLogEventWire> output) const noexcept;
private:
    const socket::SocketRegistry& registry_;
    const diagnostics::RingLogger& logger_;
    mutable std::mutex scratch_mutex_;
    mutable std::array<diagnostics::LogEvent,kMaxRecentLogEvents> scratch_{};
};
}
