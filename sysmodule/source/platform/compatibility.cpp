#include <nxless/sys/platform/compatibility.hpp>
#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere.hpp>
#endif
namespace nxless::sys::platform {
HosVersion QueryHosVersion() noexcept {
#if defined(ATMOSPHERE_OS_HORIZON)
    const std::uint32_t packed = static_cast<std::uint32_t>(ams::hos::GetVersion());
    return {(packed >> 24U) & 0xFFU, (packed >> 16U) & 0xFFU, (packed >> 8U) & 0xFFU};
#else
    return {};
#endif
}
}
