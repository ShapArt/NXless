#pragma once

#include <cstdint>
#include <optional>
#include <string_view>

namespace nxless::config {

struct Phase0Config {
    static constexpr std::uint32_t kVersion = 1;
    bool diagnostics_enabled{true};
};

enum class ConfigError : std::uint8_t {
    TooLarge,
    UnsupportedVersion,
    Malformed,
};

struct ParseResult {
    Phase0Config config{};
    std::optional<ConfigError> error{};
    bool safe_defaults_used{false};
};

inline constexpr std::size_t kMaxConfigBytes = 64 * 1024;
inline constexpr std::size_t kMaxConfigLineBytes = 1024;

ParseResult ParsePhase0Config(std::string_view bytes) noexcept;

} // namespace nxless::config
