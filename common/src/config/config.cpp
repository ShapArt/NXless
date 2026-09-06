#include <nxless/config/config.hpp>

#include <cctype>
#include <limits>

namespace nxless::config {
namespace {

std::string_view Trim(std::string_view value) noexcept {
    while (!value.empty() && (value.front() == ' ' || value.front() == '\t' || value.front() == '\r')) {
        value.remove_prefix(1);
    }
    while (!value.empty() && (value.back() == ' ' || value.back() == '\t' || value.back() == '\r')) {
        value.remove_suffix(1);
    }
    return value;
}

bool IsAsciiToken(std::string_view value) noexcept {
    for (const char raw : value) {
        const auto ch = static_cast<unsigned char>(raw);
        if (ch == 0 || ch >= 0x80) {
            return false;
        }
        if (!(std::isalnum(ch) != 0 || ch == '_')) {
            return false;
        }
    }
    return !value.empty();
}

bool ParseU32(std::string_view value, std::uint32_t& out) noexcept {
    if (value.empty()) {
        return false;
    }
    std::uint32_t parsed = 0;
    for (const char raw : value) {
        const auto ch = static_cast<unsigned char>(raw);
        if (ch < static_cast<unsigned char>('0') || ch > static_cast<unsigned char>('9')) {
            return false;
        }
        const std::uint32_t digit = static_cast<std::uint32_t>(ch - static_cast<unsigned char>('0'));
        if (parsed > (std::numeric_limits<std::uint32_t>::max() - digit) / 10U) {
            return false;
        }
        parsed = parsed * 10U + digit;
    }
    out = parsed;
    return true;
}

ParseResult SafeError(const ConfigError error) noexcept {
    return ParseResult{Phase0Config{}, error, true};
}

} // namespace

ParseResult ParsePhase0Config(const std::string_view bytes) noexcept {
    if (bytes.size() > kMaxConfigBytes) {
        return SafeError(ConfigError::TooLarge);
    }
    if (bytes.empty()) {
        return SafeError(ConfigError::Malformed);
    }

    Phase0Config parsed{};
    bool seen_version = false;
    bool seen_diagnostics = false;
    std::size_t cursor = 0;

    while (cursor <= bytes.size()) {
        const std::size_t newline = bytes.find('\n', cursor);
        const std::size_t end = newline == std::string_view::npos ? bytes.size() : newline;
        if (end - cursor > kMaxConfigLineBytes) {
            return SafeError(ConfigError::Malformed);
        }

        std::string_view line = Trim(bytes.substr(cursor, end - cursor));
        if (!line.empty() && line.front() != '#') {
            if (line.find('\0') != std::string_view::npos) {
                return SafeError(ConfigError::Malformed);
            }
            const std::size_t equals = line.find('=');
            if (equals == std::string_view::npos || line.find('=', equals + 1) != std::string_view::npos) {
                return SafeError(ConfigError::Malformed);
            }
            const std::string_view key = Trim(line.substr(0, equals));
            const std::string_view value = Trim(line.substr(equals + 1));
            if (!IsAsciiToken(key) || value.empty()) {
                return SafeError(ConfigError::Malformed);
            }

            if (key == "version") {
                if (seen_version) {
                    return SafeError(ConfigError::Malformed);
                }
                seen_version = true;
                std::uint32_t version = 0;
                if (!ParseU32(value, version)) {
                    return SafeError(ConfigError::Malformed);
                }
                if (version != Phase0Config::kVersion) {
                    return SafeError(ConfigError::UnsupportedVersion);
                }
            } else if (key == "diagnostics_enabled") {
                if (seen_diagnostics) {
                    return SafeError(ConfigError::Malformed);
                }
                seen_diagnostics = true;
                if (value == "true") {
                    parsed.diagnostics_enabled = true;
                } else if (value == "false") {
                    parsed.diagnostics_enabled = false;
                } else {
                    return SafeError(ConfigError::Malformed);
                }
            } else {
                return SafeError(ConfigError::Malformed);
            }
        }

        if (newline == std::string_view::npos) {
            break;
        }
        cursor = newline + 1;
    }

    if (!seen_version) {
        return SafeError(ConfigError::Malformed);
    }
    return ParseResult{parsed, std::nullopt, false};
}

} // namespace nxless::config
