#include <nxless/diagnostics/ring_logger.hpp>

#include <algorithm>
#include <cstring>

namespace nxless::diagnostics {

void RingLogger::Push(const LogLevel level, const std::string_view already_redacted) noexcept {
    std::scoped_lock lock(mutex_);

    std::size_t index = 0;
    if (size_ < kEventCapacity) {
        index = (head_ + size_) % kEventCapacity;
        ++size_;
    } else {
        index = head_;
        head_ = (head_ + 1) % kEventCapacity;
        ++dropped_count_;
    }

    LogEvent& event = events_[index];
    event = {};
    event.sequence = next_sequence_++;
    if (next_sequence_ == 0) {
        next_sequence_ = 1;
    }
    event.level = level;

    const std::size_t copy_size = std::min(already_redacted.size(), event.message.size() - 1);
    if (copy_size != 0) {
        std::memcpy(event.message.data(), already_redacted.data(), copy_size);
    }
    event.message[copy_size] = '\0';
}

std::vector<LogEvent> RingLogger::Snapshot(const std::size_t max_events) const {
    std::scoped_lock lock(mutex_);
    const std::size_t count = std::min(max_events, size_);
    std::vector<LogEvent> snapshot;
    snapshot.reserve(count);

    const std::size_t skip = size_ - count;
    for (std::size_t i = 0; i < count; ++i) {
        const std::size_t index = (head_ + skip + i) % kEventCapacity;
        snapshot.push_back(events_[index]);
    }
    return snapshot;
}

std::size_t RingLogger::SnapshotInto(const std::span<LogEvent> output) const noexcept {
    std::scoped_lock lock(mutex_);
    const std::size_t count = std::min(output.size(), size_);
    const std::size_t skip = size_ - count;
    for (std::size_t i = 0; i < count; ++i) {
        const std::size_t index = (head_ + skip + i) % kEventCapacity;
        output[i] = events_[index];
    }
    return count;
}

std::uint64_t RingLogger::DroppedCount() const noexcept {
    std::scoped_lock lock(mutex_);
    return dropped_count_;
}

std::size_t RingLogger::StoredCount() const noexcept {
    std::scoped_lock lock(mutex_);
    return size_;
}

} // namespace nxless::diagnostics
