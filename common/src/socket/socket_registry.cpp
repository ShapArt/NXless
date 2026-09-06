#include <nxless/socket/socket_registry.hpp>

#include <algorithm>

namespace nxless::socket {

bool SocketRegistry::ClientExistsUnlocked(const ClientContextId client) const noexcept {
    return std::any_of(clients_.begin(), clients_.end(), [client](const ClientSlot& slot) {
        return slot.active && slot.id == client;
    });
}

SocketRegistry::SocketSlot* SocketRegistry::FindSlotUnlocked(const ClientContextId client,
                                                             const int fd) noexcept {
    const auto it = std::find_if(sockets_.begin(), sockets_.end(), [client, fd](const SocketSlot& slot) {
        return slot.active && slot.state.key.client == client && slot.state.key.fd == fd;
    });
    return it == sockets_.end() ? nullptr : &*it;
}

const SocketRegistry::SocketSlot* SocketRegistry::FindSlotUnlocked(const ClientContextId client,
                                                                   const int fd) const noexcept {
    const auto it = std::find_if(sockets_.cbegin(), sockets_.cend(), [client, fd](const SocketSlot& slot) {
        return slot.active && slot.state.key.client == client && slot.state.key.fd == fd;
    });
    return it == sockets_.cend() ? nullptr : &*it;
}

SocketGeneration SocketRegistry::NextGenerationUnlocked() noexcept {
    const SocketGeneration current = next_generation_;
    ++next_generation_;
    if (next_generation_ == 0) {
        next_generation_ = 1;
    }
    return current == 0 ? SocketGeneration{1} : current;
}

bool SocketRegistry::RegisterClient(const ClientContextId client) noexcept {
    if (client == 0) {
        return false;
    }
    std::scoped_lock lock(mutex_);
    if (ClientExistsUnlocked(client)) {
        return true;
    }
    const auto it = std::find_if(clients_.begin(), clients_.end(), [](const ClientSlot& slot) {
        return !slot.active;
    });
    if (it == clients_.end()) {
        return false;
    }
    it->active = true;
    it->id = client;
    const auto active_clients = static_cast<std::size_t>(
        std::count_if(clients_.cbegin(), clients_.cend(), [](const ClientSlot& slot) { return slot.active; }));
    client_high_water_mark_ = std::max(client_high_water_mark_, active_clients);
    return true;
}

void SocketRegistry::UnregisterClient(const ClientContextId client) noexcept {
    std::scoped_lock lock(mutex_);
    for (SocketSlot& slot : sockets_) {
        if (slot.active && slot.state.key.client == client) {
            slot.active = false;
            slot.state = {};
            if (active_socket_count_ > 0) {
                --active_socket_count_;
            }
        }
    }
    for (ClientSlot& slot : clients_) {
        if (slot.active && slot.id == client) {
            slot.active = false;
            slot.id = 0;
            break;
        }
    }
}

std::optional<SocketKey> SocketRegistry::OnSocketCreated(const ClientContextId client,
                                                         const int fd) noexcept {
    std::scoped_lock lock(mutex_);
    if (!ClientExistsUnlocked(client) || fd < 0) {
        return std::nullopt;
    }
    if (const SocketSlot* existing = FindSlotUnlocked(client, fd); existing != nullptr) {
        return existing->state.key;
    }
    const auto it = std::find_if(sockets_.begin(), sockets_.end(), [](const SocketSlot& slot) {
        return !slot.active;
    });
    if (it == sockets_.end()) {
        return std::nullopt;
    }

    const SocketKey key{client, fd, NextGenerationUnlocked()};
    it->active = true;
    it->state = SocketState{key, InterceptionTag::Transparent};
    ++active_socket_count_;
    high_water_mark_ = std::max(high_water_mark_, active_socket_count_);
    return key;
}

bool SocketRegistry::OnSocketClosed(const ClientContextId client, const int fd) noexcept {
    std::scoped_lock lock(mutex_);
    SocketSlot* slot = FindSlotUnlocked(client, fd);
    if (slot == nullptr) {
        return false;
    }
    slot->active = false;
    slot->state = {};
    if (active_socket_count_ > 0) {
        --active_socket_count_;
    }
    return true;
}

std::optional<SocketState> SocketRegistry::Find(const ClientContextId client, const int fd) const noexcept {
    std::scoped_lock lock(mutex_);
    const SocketSlot* slot = FindSlotUnlocked(client, fd);
    if (slot == nullptr) {
        return std::nullopt;
    }
    return slot->state;
}

bool SocketRegistry::SetTag(const ClientContextId client, const int fd, const InterceptionTag tag) noexcept {
    std::scoped_lock lock(mutex_);
    SocketSlot* slot = FindSlotUnlocked(client, fd);
    if (slot == nullptr) {
        return false;
    }
    slot->state.tag = tag;
    return true;
}

std::size_t SocketRegistry::ActiveClientCount() const noexcept {
    std::scoped_lock lock(mutex_);
    return static_cast<std::size_t>(std::count_if(clients_.cbegin(), clients_.cend(), [](const ClientSlot& slot) {
        return slot.active;
    }));
}

std::size_t SocketRegistry::ClientHighWaterMark() const noexcept {
    std::scoped_lock lock(mutex_);
    return client_high_water_mark_;
}

std::size_t SocketRegistry::ActiveSocketCount() const noexcept {
    std::scoped_lock lock(mutex_);
    return active_socket_count_;
}

std::size_t SocketRegistry::ClientSocketCount(const ClientContextId client) const noexcept {
    std::scoped_lock lock(mutex_);
    return static_cast<std::size_t>(std::count_if(sockets_.cbegin(), sockets_.cend(), [client](const SocketSlot& slot) {
        return slot.active && slot.state.key.client == client;
    }));
}

std::size_t SocketRegistry::HighWaterMark() const noexcept {
    std::scoped_lock lock(mutex_);
    return high_water_mark_;
}

} // namespace nxless::socket
