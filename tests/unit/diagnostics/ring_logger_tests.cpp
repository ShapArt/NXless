#include <catch2/catch_test_macros.hpp>
#include <string>
#include <nxless/diagnostics/ring_logger.hpp>

using namespace nxless::diagnostics;

TEST_CASE("logger remains bounded under flood", "[ring_logger]") {
    RingLogger logger;
    const auto cap = RingLogger::EventCapacity();
    for (std::size_t i = 0; i < cap * 10; ++i) {
        logger.Push(LogLevel::Info, "sanitized event");
    }
    const auto snapshot = logger.Snapshot(cap * 2);
    REQUIRE(snapshot.size() == cap);
    REQUIRE(logger.DroppedCount() == cap * 9);
    REQUIRE(logger.StoredCount() == cap);
}

TEST_CASE("message is truncated and nul terminated", "[ring_logger]") {
    RingLogger logger;
    logger.Push(LogLevel::Warning, std::string(1000, 'x'));
    const auto snapshot = logger.Snapshot(1);
    REQUIRE(snapshot.size() == 1);
    REQUIRE(snapshot[0].message.back() == '\0');
}
