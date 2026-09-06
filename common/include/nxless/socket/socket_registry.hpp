#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>

#include <nxless/socket/socket_state.hpp>

namespace nxless::socket {

enum class RegistryError : std::uint8_t {
    CapacityExceeded,
    ClientUnknown,
    SocketUnknown,
};

class SocketRegistry {
public:
    static constexpr std::size_t kMaxSockets = 512;
    static constexpr std::size_t kMaxClients = 64;

    bool RegisterClient(ClientContextId client) noexcept;
    void UnregisterClient(ClientContextId client) noexcept;

    std::optional<SocketKey> OnSocketCreated(ClientContextId client, int fd) noexcept;
    bool OnSocketClosed(ClientContextId client, int fd) noexcept;

    // Snapshot semantics: callers never retain pointers into registry storage.
    std::optional<SocketState> Find(ClientContextId client, int fd) const noexcept;
    bool SetTag(ClientContextId client, int fd, InterceptionTag tag) noexcept;

    std::size_t ActiveClientCount() const noexcept;
    std::size_t ClientHighWaterMark() const noexcept;
    std::size_t ActiveSocketCount() const noexcept;
    std::size_t ClientSocketCount(ClientContextId client) const noexcept;
    std::size_t HighWaterMark() const noexcept;

private:
    struct ClientSlot {
        bool active{false};
        ClientContextId id{};
    };

    struct SocketSlot {
        bool active{false};
        SocketState state{};
    };

    bool ClientExistsUnlocked(ClientContextId client) const noexcept;
    SocketSlot* FindSlotUnlocked(ClientContextId client, int fd) noexcept;
    const SocketSlot* FindSlotUnlocked(ClientContextId client, int fd) const noexcept;
    SocketGeneration NextGenerationUnlocked() noexcept;

    mutable std::mutex mutex_;
    std::array<ClientSlot, kMaxClients> clients_{};
    std::array<SocketSlot, kMaxSockets> sockets_{};
    std::size_t client_high_water_mark_{0};
    std::size_t active_socket_count_{0};
    std::size_t high_water_mark_{0};
    SocketGeneration next_generation_{1};
};

} // namespace nxless::socket
