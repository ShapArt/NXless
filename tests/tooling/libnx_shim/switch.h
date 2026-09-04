#pragma once
#include <cstdint>
#include <cstddef>

using Result = std::uint32_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;

#define R_FAILED(rc) ((rc) != 0U)
#define R_SUCCEEDED(rc) ((rc) == 0U)

struct Service {};
struct PadState {};
inline constexpr int HidNpadStyleSet_NpadStandard = 0;
inline constexpr u64 HidNpadButton_Plus = 1ULL;

inline void consoleInit(void*) {}
inline void consoleExit(void*) {}
inline void consoleUpdate(void*) {}
inline void padConfigureInput(int, int) {}
inline void padInitializeDefault(PadState*) {}
inline void padUpdate(PadState*) {}
inline u64 padGetButtonsDown(PadState*) { return HidNpadButton_Plus; }
inline bool appletMainLoop() { return false; }
inline Result smGetService(Service*, const char*) { return 0U; }
inline void serviceClose(Service*) {}
inline Result socketInitializeDefault() { return 0U; }
inline void socketExit() {}

#define serviceDispatchOut(service, cmd, out) \
    (static_cast<void>(service), static_cast<void>(cmd), static_cast<void>(sizeof(out)), Result{0})
