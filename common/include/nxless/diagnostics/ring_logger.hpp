#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <string_view>
#include <span>
#include <vector>

#include <nxless/diagnostics/log_event.hpp>

namespace nxless::diagnostics {

class RingLogger {
public:
    static constexpr std::size_t kCapacityBytes = 256 * 1024;
    static constexpr std::size_t kEventCapacity = kCapacityBytes / sizeof(LogEvent);

    static constexpr std::size_t EventCapacity() noexcept { return kEventCapacity; }

    void Push(LogLevel level, std::string_view already_redacted) noexcept;
    std::vector<LogEvent> Snapshot(std::size_t max_events) const;
    std::size_t SnapshotInto(std::span<LogEvent> output) const noexcept;
    std::uint64_t DroppedCount() const noexcept;
    std::size_t StoredCount() const noexcept;

private:
    mutable std::mutex mutex_;
    std::array<LogEvent, kEventCapacity> events_{};
    std::size_t head_{0};
    std::size_t size_{0};
    std::uint64_t next_sequence_{1};
    std::uint64_t dropped_count_{0};
};

static_assert(RingLogger::kEventCapacity > 0);
static_assert(RingLogger::kEventCapacity * sizeof(LogEvent) <= RingLogger::kCapacityBytes);

} // namespace nxless::diagnostics
