#include <nxless/diagnostics/secret_redactor.hpp>

#include <algorithm>
#include <array>
#include <cctype>

namespace nxless::diagnostics {
namespace {

constexpr std::string_view kVlessReplacement = "[REDACTED_VLESS_URI]";
constexpr std::string_view kValueReplacement = "[REDACTED]";

char Lower(const char ch) noexcept {
    return static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
}

bool IStartsWithAt(const std::string_view text, const std::size_t pos, const std::string_view needle) {
    if (pos > text.size() || needle.size() > text.size() - pos) {
        return false;
    }
    for (std::size_t i = 0; i < needle.size(); ++i) {
        if (Lower(text[pos + i]) != Lower(needle[i])) {
            return false;
        }
    }
    return true;
}

bool IsQuerySecretKey(const std::string_view key) {
    static constexpr std::array<std::string_view, 9> keys{
        "token", "auth", "authorization", "password", "passwd", "secret", "key", "uuid", "sid"};
    for (const auto candidate : keys) {
        if (key.size() != candidate.size()) {
            continue;
        }
        bool same = true;
        for (std::size_t i = 0; i < key.size(); ++i) {
            if (Lower(key[i]) != candidate[i]) {
                same = false;
                break;
            }
        }
        if (same) {
            return true;
        }
    }
    return false;
}

std::size_t FindTokenEnd(const std::string_view input, const std::size_t start) {
    std::size_t pos = start;
    while (pos < input.size()) {
        const char ch = input[pos];
        if (std::isspace(static_cast<unsigned char>(ch)) != 0 || ch == '"' || ch == '\'' || ch == ')' || ch == ']') {
            break;
        }
        ++pos;
    }
    return pos;
}

std::string RedactVless(std::string_view input) {
    std::string output;
    output.reserve(std::min(input.size(), SecretRedactor::kMaxInputBytes) + 32);
    for (std::size_t i = 0; i < input.size();) {
        if (IStartsWithAt(input, i, "vless://")) {
            output.append(kVlessReplacement);
            i = FindTokenEnd(input, i);
            continue;
        }
        output.push_back(input[i]);
        ++i;
    }
    return output;
}

std::string RedactAuthorization(std::string_view input) {
    std::string output;
    output.reserve(input.size());
    std::size_t cursor = 0;
    while (cursor < input.size()) {
        const auto line_end = input.find('\n', cursor);
        const auto end = line_end == std::string_view::npos ? input.size() : line_end;
        const auto line = input.substr(cursor, end - cursor);
        if (IStartsWithAt(line, 0, "authorization:")) {
            output.append("Authorization: ");
            output.append(kValueReplacement);
        } else {
            output.append(line);
        }
        if (line_end != std::string_view::npos) {
            output.push_back('\n');
            cursor = line_end + 1;
        } else {
            cursor = input.size();
        }
    }
    return output;
}

std::string RedactUserInfo(std::string_view input) {
    std::string output(input);
    std::size_t scheme = 0;
    while ((scheme = output.find("://", scheme)) != std::string::npos) {
        const std::size_t authority_start = scheme + 3;
        const std::size_t authority_end = output.find_first_of("/ ?#\n\r\t", authority_start);
        const std::size_t end = authority_end == std::string::npos ? output.size() : authority_end;
        const std::size_t at = output.find('@', authority_start);
        if (at != std::string::npos && at < end) {
            const std::string replacement = std::string(kValueReplacement) + "@";
            output.replace(authority_start, at - authority_start + 1, replacement);
            scheme = authority_start + replacement.size();
        } else {
            scheme = end;
        }
    }
    return output;
}

std::string RedactQueryValues(std::string_view input) {
    std::string output;
    output.reserve(input.size());
    std::size_t i = 0;
    while (i < input.size()) {
        if (input[i] != '?' && input[i] != '&') {
            output.push_back(input[i++]);
            continue;
        }
        const char delimiter = input[i++];
        output.push_back(delimiter);
        const std::size_t key_start = i;
        while (i < input.size() && input[i] != '=' && input[i] != '&' && input[i] != '#' &&
               std::isspace(static_cast<unsigned char>(input[i])) == 0) {
            ++i;
        }
        const auto key = input.substr(key_start, i - key_start);
        output.append(key);
        if (i >= input.size() || input[i] != '=') {
            continue;
        }
        output.push_back('=');
        ++i;
        const std::size_t value_start = i;
        while (i < input.size() && input[i] != '&' && input[i] != '#' &&
               std::isspace(static_cast<unsigned char>(input[i])) == 0) {
            ++i;
        }
        if (IsQuerySecretKey(key)) {
            output.append(kValueReplacement);
        } else {
            output.append(input.substr(value_start, i - value_start));
        }
    }
    return output;
}

} // namespace

std::string SecretRedactor::Redact(const std::string_view input) {
    const std::size_t capped_size = std::min(input.size(), kMaxInputBytes);
    const std::string_view capped = input.substr(0, capped_size);

    auto output = RedactVless(capped);
    output = RedactAuthorization(output);
    output = RedactUserInfo(output);
    output = RedactQueryValues(output);

    if (input.size() > kMaxInputBytes) {
        output.append(" [TRUNCATED]");
    }
    return output;
}

} // namespace nxless::diagnostics
