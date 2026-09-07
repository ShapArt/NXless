#include <nxless/sys/config/sd_config_store.hpp>

#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere.hpp>
#endif

namespace nxless::sys::config {
#if defined(ATMOSPHERE_OS_HORIZON)
SdLoadResult SdConfigStore::Load(FsFileSystem* sd_fs) noexcept {
    SdLoadResult result{};
    if (sd_fs == nullptr) {
        return result;
    }

    FsFile flag{};
    const ::Result flag_rc = fsFsOpenFile(sd_fs, kDisableFlagFsPath, FsOpenMode_Read, &flag);
    if (R_SUCCEEDED(flag_rc)) {
        result.disable_probe_ok = true;
        result.disable_flag_present = true;
        fsFileClose(&flag);
    } else if (ams::fs::ResultPathNotFound::Includes(flag_rc)) {
        result.disable_probe_ok = true;
    } else {
        return result;
    }

    FsFile file{};
    const ::Result open_rc = fsFsOpenFile(sd_fs, kConfigFsPath, FsOpenMode_Read, &file);
    if (ams::fs::ResultPathNotFound::Includes(open_rc)) {
        result.config_status = SdReadStatus::Missing;
        result.parsed = {};
        return result;
    }
    if (R_FAILED(open_rc)) {
        return result;
    }

    s64 size = 0;
    const ::Result size_rc = fsFileGetSize(&file, &size);
    if (R_FAILED(size_rc) || size < 0) {
        fsFileClose(&file);
        return result;
    }
    if (static_cast<std::uint64_t>(size) > workspace_.size()) {
        fsFileClose(&file);
        result.config_status = SdReadStatus::TooLarge;
        return result;
    }

    const auto read_size = static_cast<std::uint64_t>(size);
    std::uint64_t bytes_read = 0;
    const ::Result read_rc = fsFileRead(
        &file,
        0,
        workspace_.data(),
        read_size,
        FsReadOption_None,
        &bytes_read);
    fsFileClose(&file);
    if (R_FAILED(read_rc) || bytes_read != read_size) {
        return result;
    }

    result.config_status = SdReadStatus::Ok;
    result.parsed = nxless::config::ParsePhase0Config(
        std::string_view(workspace_.data(), static_cast<std::size_t>(size)));
    return result;
}
#else
SdLoadResult SdConfigStore::Load() noexcept {
    SdLoadResult result{};
    result.disable_probe_ok = true;
    result.config_status = SdReadStatus::Missing;
    result.parsed = {};
    return result;
}
#endif
}
