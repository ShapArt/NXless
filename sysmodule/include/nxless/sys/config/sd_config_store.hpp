#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <nxless/config/config.hpp>

#if defined(ATMOSPHERE_OS_HORIZON)
#include <switch.h>
#endif

namespace nxless::sys::config {
inline constexpr const char* kDisableFlagPath = "sdmc:/config/nxless/disable.flag";
inline constexpr const char* kConfigPath = "sdmc:/config/nxless/config.toml";
inline constexpr const char* kDisableFlagFsPath = "/config/nxless/disable.flag";
inline constexpr const char* kConfigFsPath = "/config/nxless/config.toml";

enum class SdReadStatus : std::uint8_t { Ok, Missing, TooLarge, IoError };
struct SdLoadResult {
    bool disable_probe_ok{false};
    bool disable_flag_present{false};
    SdReadStatus config_status{SdReadStatus::IoError};
    nxless::config::ParseResult parsed{};
};
class SdConfigStore {
public:
    static constexpr std::size_t kWorkspaceBytes = nxless::config::kMaxConfigBytes;
#if defined(ATMOSPHERE_OS_HORIZON)
    SdLoadResult Load(FsFileSystem* sd_fs) noexcept;
#else
    SdLoadResult Load() noexcept;
#endif
private:
    std::array<char, kWorkspaceBytes> workspace_{};
};
}
