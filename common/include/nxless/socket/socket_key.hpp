#pragma once

#include <cstdint>

namespace nxless::socket {

using ClientContextId = std::uint64_t;
using SocketGeneration = std::uint32_t;

struct SocketKey {
    ClientContextId client{};
    int fd{-1};
    SocketGeneration generation{};

    friend bool operator==(const SocketKey&, const SocketKey&) = default;
};

} // namespace nxless::socket
