#pragma once
#include <cstdint>
namespace nxless::sys::platform {
struct HosVersion { std::uint32_t major{}, minor{}, patch{}; };
constexpr bool IsPhase0SupportedHos(HosVersion v) noexcept { return v.major==22U && v.minor==5U && v.patch==0U; }
HosVersion QueryHosVersion() noexcept;
}
