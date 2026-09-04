#pragma once
#include <cstddef>
#include <cstdint>

using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s64 = std::int64_t;
using Result = std::uint32_t;

#define R_SUCCEEDED(rc) ((rc) == 0)
#define R_FAILED(rc) ((rc) != 0)

struct Service { std::uintptr_t opaque; };
struct FsFileSystem { Service s; };
struct FsFile { Service s; };

inline constexpr u32 FsOpenMode_Read = 1u;
inline constexpr u32 FsReadOption_None = 0u;

Result fsFsOpenFile(FsFileSystem* fs, const char* path, u32 mode, FsFile* out);
Result fsFileGetSize(FsFile* file, s64* out);
Result fsFileRead(FsFile* file, s64 offset, void* buffer, u64 size, u32 option, u64* out_read);
void fsFileClose(FsFile* file);
