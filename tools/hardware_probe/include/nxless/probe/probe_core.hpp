#pragma once

#include <array>
#include <cstdint>
#include <string_view>

#include <nxless/ipc/control_protocol.hpp>

namespace nxless::probe {

struct ProbeConfig {
    std::array<char, 64> host{};
    std::uint16_t tcp_port{5001};
    std::uint16_t udp_port{5002};
    std::uint32_t concurrent{4};
};

bool ParseConfigText(std::string_view text, ProbeConfig& out) noexcept;
const char* RuntimeModeName(nxless::ipc::RuntimeMode mode) noexcept;

} // namespace nxless::probe
