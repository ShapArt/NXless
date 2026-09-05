#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
namespace nxless::sys::bsd::hos_22_5_0 {
enum class Handling : std::uint8_t { RawForward, ForwardWithStateHook };
struct CommandInfo { std::uint32_t id{}; Handling handling{Handling::RawForward}; };
inline constexpr std::array<CommandInfo,46> kCommandManifest{{
 {0,Handling::RawForward},{1,Handling::RawForward},{2,Handling::ForwardWithStateHook},{3,Handling::ForwardWithStateHook},
 {4,Handling::RawForward},{5,Handling::RawForward},{6,Handling::RawForward},{7,Handling::RawForward},{8,Handling::RawForward},{9,Handling::RawForward},
 {10,Handling::RawForward},{11,Handling::RawForward},{12,Handling::ForwardWithStateHook},{13,Handling::RawForward},{14,Handling::RawForward},
 {15,Handling::RawForward},{16,Handling::RawForward},{17,Handling::RawForward},{18,Handling::RawForward},{19,Handling::RawForward},
 {20,Handling::RawForward},{21,Handling::RawForward},{22,Handling::RawForward},{23,Handling::RawForward},{24,Handling::RawForward},
 {25,Handling::RawForward},{26,Handling::ForwardWithStateHook},{27,Handling::ForwardWithStateHook},{28,Handling::RawForward},{29,Handling::RawForward},
 {30,Handling::RawForward},{31,Handling::RawForward},{32,Handling::RawForward},{33,Handling::RawForward},{34,Handling::RawForward},
 {35,Handling::RawForward},{36,Handling::RawForward},{37,Handling::RawForward},{38,Handling::RawForward},{39,Handling::RawForward},
 {40,Handling::RawForward},{41,Handling::RawForward},{42,Handling::RawForward},{43,Handling::RawForward},{200,Handling::RawForward},{201,Handling::RawForward}
}};
consteval bool ManifestIdsUnique() { for(std::size_t i=0;i<kCommandManifest.size();++i) for(std::size_t j=i+1;j<kCommandManifest.size();++j) if(kCommandManifest[i].id==kCommandManifest[j].id) return false; return true; }
static_assert(ManifestIdsUnique());
constexpr Handling HandlingFor(std::uint32_t id) noexcept { for(const auto& c:kCommandManifest) if(c.id==id) return c.handling; return Handling::RawForward; }
}
