#pragma once

#include <atomic>
#include <cstdint>

#include <nxless/ipc/control_protocol.hpp>

namespace nxless::ipc {

struct ControlStateSnapshot {
    RuntimeMode mode{RuntimeMode::ErrorPassthrough};
    std::int32_t last_internal_error{};
};

class ControlState {
public:
    constexpr ControlState() noexcept = default;

    void Store(RuntimeMode mode, std::int32_t last_internal_error) noexcept {
        packed_.store(Pack(mode, last_internal_error), std::memory_order_release);
    }

    void SetMode(RuntimeMode mode) noexcept {
        auto current = packed_.load(std::memory_order_relaxed);
        while (!packed_.compare_exchange_weak(
            current,
            Pack(mode, DecodeError(current)),
            std::memory_order_release,
            std::memory_order_relaxed)) {
        }
    }

    void SetLastInternalError(std::int32_t last_internal_error) noexcept {
        auto current = packed_.load(std::memory_order_relaxed);
        while (!packed_.compare_exchange_weak(
            current,
            Pack(DecodeMode(current), last_internal_error),
            std::memory_order_release,
            std::memory_order_relaxed)) {
        }
    }

    [[nodiscard]] ControlStateSnapshot Load() const noexcept {
        const auto value = packed_.load(std::memory_order_acquire);
        return {DecodeMode(value), DecodeError(value)};
    }

private:
    static constexpr std::uint64_t Pack(RuntimeMode mode, std::int32_t last_internal_error) noexcept {
        return static_cast<std::uint64_t>(static_cast<std::uint8_t>(mode)) |
               (static_cast<std::uint64_t>(static_cast<std::uint32_t>(last_internal_error)) << 32U);
    }

    static constexpr RuntimeMode DecodeMode(std::uint64_t packed) noexcept {
        return static_cast<RuntimeMode>(static_cast<std::uint8_t>(packed & 0xFFU));
    }

    static constexpr std::int32_t DecodeError(std::uint64_t packed) noexcept {
        return static_cast<std::int32_t>(static_cast<std::uint32_t>(packed >> 32U));
    }

    std::atomic<std::uint64_t> packed_{Pack(RuntimeMode::ErrorPassthrough, 0)};
};

static_assert(std::atomic<std::uint64_t>::is_always_lock_free);

} // namespace nxless::ipc
