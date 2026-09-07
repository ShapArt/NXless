#pragma once

#include <array>
#include <cstdint>

namespace nxless::diagnostics {

enum class LogLevel : std::uint8_t {
    Debug,
    Info,
    Warning,
    Error,
};

struct LogEvent {
    std::uint64_t sequence{};
    LogLevel level{LogLevel::Info};
    std::array<char, 160> message{};
};

} // namespace nxless::diagnostics
