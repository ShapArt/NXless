#pragma once

#include <string>
#include <string_view>

namespace nxless::diagnostics {

class SecretRedactor {
public:
    static constexpr std::size_t kMaxInputBytes = 4096;
    static std::string Redact(std::string_view input);
};

} // namespace nxless::diagnostics
