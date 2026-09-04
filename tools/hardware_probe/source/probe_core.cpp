#include <nxless/probe/probe_core.hpp>

#include <charconv>
#include <cstddef>
#include <cstring>

namespace nxless::probe {
namespace {

std::string_view Trim(std::string_view s) noexcept {
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t' || s.front() == '\r')) {
        s.remove_prefix(1);
    }
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t' || s.back() == '\r')) {
        s.remove_suffix(1);
    }
    return s;
}

bool ParseUnsigned(std::string_view s, std::uint32_t& out) noexcept {
    if (s.empty()) {
        return false;
    }
    std::uint32_t value{};
    const auto* first = s.data();
    const auto* last = s.data() + s.size();
    const auto [ptr, ec] = std::from_chars(first, last, value, 10);
    if (ec != std::errc{} || ptr != last) {
        return false;
    }
    out = value;
    return true;
}

bool ValidateIpv4(std::string_view s) noexcept {
    std::size_t start = 0;
    int parts = 0;
    while (start <= s.size()) {
        const std::size_t dot = s.find('.', start);
        const std::size_t end = dot == std::string_view::npos ? s.size() : dot;
        const auto part = s.substr(start, end - start);
        std::uint32_t value{};
        if (part.empty() || part.size() > 3 || !ParseUnsigned(part, value) || value > 255) {
            return false;
        }
        ++parts;
        if (dot == std::string_view::npos) {
            break;
        }
        start = dot + 1;
    }
    return parts == 4;
}

bool CopyHost(std::string_view host, ProbeConfig& out) noexcept {
    if (!ValidateIpv4(host) || host.size() >= out.host.size()) {
        return false;
    }
    out.host.fill('\0');
    std::memcpy(out.host.data(), host.data(), host.size());
    return true;
}

} // namespace

bool ParseConfigText(const std::string_view text, ProbeConfig& out) noexcept {
    ProbeConfig parsed{};
    bool have_host = false;
    std::size_t pos = 0;
    while (pos <= text.size()) {
        const std::size_t nl = text.find('\n', pos);
        const std::size_t end = nl == std::string_view::npos ? text.size() : nl;
        auto line = Trim(text.substr(pos, end - pos));
        if (!line.empty() && line.front() != '#') {
            const std::size_t eq = line.find('=');
            if (eq == std::string_view::npos) {
                return false;
            }
            const auto key = Trim(line.substr(0, eq));
            const auto value = Trim(line.substr(eq + 1));
            std::uint32_t number{};
            if (key == "host") {
                if (!CopyHost(value, parsed)) {
                    return false;
                }
                have_host = true;
            } else if (key == "tcp_port") {
                if (!ParseUnsigned(value, number) || number == 0 || number > 65535) {
                    return false;
                }
                parsed.tcp_port = static_cast<std::uint16_t>(number);
            } else if (key == "udp_port") {
                if (!ParseUnsigned(value, number) || number == 0 || number > 65535) {
                    return false;
                }
                parsed.udp_port = static_cast<std::uint16_t>(number);
            } else if (key == "concurrent") {
                if (!ParseUnsigned(value, number) || number == 0 || number > 16) {
                    return false;
                }
                parsed.concurrent = number;
            } else {
                return false;
            }
        }
        if (nl == std::string_view::npos) {
            break;
        }
        pos = nl + 1;
    }
    if (!have_host) {
        return false;
    }
    out = parsed;
    return true;
}

const char* RuntimeModeName(const nxless::ipc::RuntimeMode mode) noexcept {
    switch (mode) {
        case nxless::ipc::RuntimeMode::SafeDisabled:
            return "SafeDisabled";
        case nxless::ipc::RuntimeMode::UnsupportedHos:
            return "UnsupportedHos";
        case nxless::ipc::RuntimeMode::DisconnectedPassthrough:
            return "DisconnectedPassthrough";
        case nxless::ipc::RuntimeMode::ErrorPassthrough:
            return "ErrorPassthrough";
    }
    return "Unknown";
}

} // namespace nxless::probe
