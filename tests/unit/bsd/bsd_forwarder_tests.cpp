#include <array>
#include <cerrno>
#include <cstring>
#include <limits>
#include <catch2/catch_test_macros.hpp>
#include <nxless/sys/bsd/bsd_forwarder.hpp>
#include <nxless/sys/bsd/hos_22_5_0/bsd_command_manifest.hpp>
namespace {
class Transport final : public nxless::sys::bsd::IOriginalBsdTransport { public:
 std::uint32_t last{}; std::size_t in_size{},out_size{},buffer_count{}; std::int32_t ret=0,err=0; std::uint32_t addrlen=16;
 std::int32_t Dispatch(const nxless::sys::bsd::IpcDispatch& r) noexcept override { last=r.command_id; in_size=r.input.size(); out_size=r.output.size(); buffer_count=r.buffer_count;
   if(r.command_id==12){ struct O{std::int32_t ret,err;std::uint32_t len;} o{ret,err,addrlen}; std::memcpy(r.output.data(),&o,sizeof(o)); }
   else { struct O{std::int32_t ret,err;} o{ret,err}; std::memcpy(r.output.data(),&o,sizeof(o)); } return 0; }
}; }
TEST_CASE("manifest is complete and hooks only stateful phase0 commands", "[bsd_manifest]") { using namespace nxless::sys::bsd::hos_22_5_0; REQUIRE(kCommandManifest.size()==46); REQUIRE(HandlingFor(2)==Handling::ForwardWithStateHook); REQUIRE(HandlingFor(3)==Handling::ForwardWithStateHook); REQUIRE(HandlingFor(12)==Handling::ForwardWithStateHook); REQUIRE(HandlingFor(26)==Handling::ForwardWithStateHook); REQUIRE(HandlingFor(14)==Handling::RawForward); REQUIRE(HandlingFor(43)==Handling::RawForward); }
TEST_CASE("socket and close use pinned command ids and ret errno layout", "[bsd_forwarder]") { Transport t; nxless::sys::bsd::BsdForwarder f(t); t.ret=-1;t.err=ECONNREFUSED; auto r=f.Socket(2,1,6); REQUIRE(t.last==2); REQUIRE(t.in_size==12); REQUIRE(t.out_size==8); REQUIRE(r.ret==-1); REQUIRE(r.bsd_errno==ECONNREFUSED); t.ret=0;t.err=99; r=f.Close(7); REQUIRE(t.last==26); REQUIRE(r.ret==0); REQUIRE(r.bsd_errno==0); }
TEST_CASE("accept preserves 12 byte output including addrlen", "[bsd_forwarder]") { Transport t; nxless::sys::bsd::BsdForwarder f(t); std::array<std::byte,32> addr{}; std::uint32_t len=0; t.ret=9;t.addrlen=16; auto r=f.Accept(3,addr,len); REQUIRE(t.last==12); REQUIRE(t.out_size==12); REQUIRE(t.buffer_count==1); REQUIRE(r.ret==9); REQUIRE(len==16); }
TEST_CASE("hipc u32 size boundary is explicit", "[bsd_forwarder]") { using nxless::sys::bsd::FitsHipcU32; REQUIRE(FitsHipcU32(std::numeric_limits<std::uint32_t>::max())); if constexpr(sizeof(std::size_t)>4) REQUIRE_FALSE(FitsHipcU32(static_cast<std::size_t>(std::numeric_limits<std::uint32_t>::max())+1ULL)); }
