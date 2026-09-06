#include <catch2/catch_test_macros.hpp>
#include <nxless/config/config.hpp>
#include <string>

using namespace nxless::config;

TEST_CASE("valid phase0 config parses", "[config]") {
    const auto r = ParsePhase0Config("version = 1\ndiagnostics_enabled = true\n");
    REQUIRE_FALSE(r.error.has_value());
    REQUIRE_FALSE(r.safe_defaults_used);
    REQUIRE(r.config.diagnostics_enabled);
}

TEST_CASE("oversized config is rejected before parsing", "[config]") {
    const std::string bytes((64 * 1024) + 1, 'x');
    const auto r = ParsePhase0Config(bytes);
    REQUIRE(r.error == ConfigError::TooLarge);
    REQUIRE(r.safe_defaults_used);
}

TEST_CASE("unsupported version uses safe defaults", "[config]") {
    const auto r = ParsePhase0Config("version = 2\ndiagnostics_enabled = false\n");
    REQUIRE(r.error == ConfigError::UnsupportedVersion);
    REQUIRE(r.safe_defaults_used);
    REQUIRE(r.config.diagnostics_enabled);
}

TEST_CASE("duplicate and unknown keys are malformed", "[config]") {
    REQUIRE(ParsePhase0Config("version=1\nversion=1\n").error == ConfigError::Malformed);
    REQUIRE(ParsePhase0Config("version=1\nunknown=true\n").error == ConfigError::Malformed);
}

TEST_CASE("line length is bounded", "[config]") {
    std::string bytes = "version=1\n" + std::string(1025, 'x');
    REQUIRE(ParsePhase0Config(bytes).error == ConfigError::Malformed);
}
