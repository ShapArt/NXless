#pragma once

#include <cstdint>
#include <nxless/socket/socket_key.hpp>

namespace nxless::socket {

enum class InterceptionTag : std::uint8_t {
    Transparent,
    ProxyCandidate,
};

struct SocketState {
    SocketKey key{};
    InterceptionTag tag{InterceptionTag::Transparent};
};

} // namespace nxless::socket
