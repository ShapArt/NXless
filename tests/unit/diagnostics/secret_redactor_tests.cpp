#include <catch2/catch_test_macros.hpp>
#include <nxless/diagnostics/secret_redactor.hpp>

using nxless::diagnostics::SecretRedactor;

TEST_CASE("vless uri is never emitted verbatim", "[redactor]") {
    constexpr auto input = "connect vless://11111111-2222-3333-4444-555555555555@example.invalid:443?security=reality&pbk=fake-key";
    const auto out = SecretRedactor::Redact(input);
    REQUIRE(out.find("11111111-2222") == std::string::npos);
    REQUIRE(out.find("fake-key") == std::string::npos);
    REQUIRE(out.find("vless://") == std::string::npos);
}

TEST_CASE("authorization header value is redacted", "[redactor]") {
    const auto out = SecretRedactor::Redact("Authorization: Bearer fake-token-123");
    REQUIRE(out.find("fake-token-123") == std::string::npos);
    REQUIRE(out.find("Authorization:") != std::string::npos);
}

TEST_CASE("userinfo password is redacted while host remains useful", "[redactor]") {
    const auto out = SecretRedactor::Redact("https://alice:fake-password@example.invalid/path");
    REQUIRE(out.find("fake-password") == std::string::npos);
    REQUIRE(out.find("alice") == std::string::npos);
    REQUIRE(out.find("example.invalid") != std::string::npos);
}

TEST_CASE("subscription query credential is redacted", "[redactor]") {
    const auto out = SecretRedactor::Redact("https://example.invalid/sub?token=fake-secret&mode=full");
    REQUIRE(out.find("fake-secret") == std::string::npos);
    REQUIRE(out.find("mode=full") != std::string::npos);
}
