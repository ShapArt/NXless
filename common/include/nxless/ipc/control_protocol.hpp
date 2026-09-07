#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace nxless::ipc {

inline constexpr std::uint32_t kControlApiMajor = 1;
inline constexpr std::uint32_t kControlApiMinor = 1;
inline constexpr std::uint32_t kMaxRecentLogEvents = 128;

enum class RuntimeMode : std::uint8_t {
    SafeDisabled,
    UnsupportedHos,
    DisconnectedPassthrough,
    ErrorPassthrough,
};

enum class ApiNegotiationResult : std::uint8_t {
    Compatible,
    MajorMismatch,
};

struct VersionInfo {
    std::uint32_t api_major;
    std::uint32_t api_minor;
    std::uint32_t sysmodule_semver_packed;
};

struct CompatibilityInfo {
    std::uint32_t hos_major;
    std::uint32_t hos_minor;
    std::uint32_t hos_patch;
    std::uint8_t bsd_mitm_supported;
    std::array<std::uint8_t, 3> reserved;
};

struct RuntimeStatus {
    RuntimeMode mode;
    std::uint8_t disable_flag_present;
    std::uint16_t client_high_water;
    std::uint32_t active_clients;
    std::uint32_t active_sockets;
    std::uint32_t socket_high_water;
    std::uint64_t log_dropped;
    std::int32_t last_internal_error;
};

constexpr ApiNegotiationResult NegotiateControlApi(const std::uint32_t requested_major) noexcept {
    return requested_major == kControlApiMajor ? ApiNegotiationResult::Compatible
                                                : ApiNegotiationResult::MajorMismatch;
}

constexpr std::uint32_t ClampRecentLogCount(const std::uint32_t requested) noexcept {
    return std::min(requested, kMaxRecentLogEvents);
}

static_assert(std::is_trivial_v<VersionInfo> && std::is_trivially_copyable_v<VersionInfo> && std::is_standard_layout_v<VersionInfo>);
static_assert(std::is_trivial_v<CompatibilityInfo> && std::is_trivially_copyable_v<CompatibilityInfo> && std::is_standard_layout_v<CompatibilityInfo>);
static_assert(std::is_trivial_v<RuntimeStatus> && std::is_trivially_copyable_v<RuntimeStatus> && std::is_standard_layout_v<RuntimeStatus>);
static_assert(sizeof(VersionInfo) == 12);
static_assert(sizeof(CompatibilityInfo) == 16);
static_assert(sizeof(RuntimeStatus) == 32);

} // namespace nxless::ipc
