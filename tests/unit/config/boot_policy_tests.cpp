#include <catch2/catch_test_macros.hpp>
#include <nxless/status/boot_policy.hpp>
#include <nxless/sys/platform/compatibility.hpp>
using namespace nxless::status;
TEST_CASE("disable flag wins", "[boot]") { auto d=DecideBoot({true,true,true,true,true,true,true}); REQUIRE_FALSE(d.bsd_mitm_allowed); REQUIRE(d.mode==nxless::ipc::RuntimeMode::SafeDisabled); }
TEST_CASE("only HOS 22.5.0 is phase0 supported", "[boot]") { using nxless::sys::platform::HosVersion; using nxless::sys::platform::IsPhase0SupportedHos; REQUIRE(IsPhase0SupportedHos(HosVersion{22,5,0})); REQUIRE_FALSE(IsPhase0SupportedHos(HosVersion{22,5,1})); REQUIRE_FALSE(IsPhase0SupportedHos(HosVersion{23,0,0})); REQUIRE_FALSE(IsPhase0SupportedHos(HosVersion{22,4,0})); }
TEST_CASE("unreadable recovery probe disables mitm", "[boot]") { auto d=DecideBoot({false,false,true,false,true,true,true}); REQUIRE_FALSE(d.bsd_mitm_allowed); REQUIRE(d.mode==nxless::ipc::RuntimeMode::ErrorPassthrough); }
TEST_CASE("missing config uses safe defaults", "[boot]") { auto d=DecideBoot({true,false,true,false,true,true,true}); REQUIRE(d.bsd_mitm_allowed); REQUIRE(d.mode==nxless::ipc::RuntimeMode::DisconnectedPassthrough); }
TEST_CASE("malformed config and missing control service disable mitm", "[boot]") { REQUIRE_FALSE(DecideBoot({true,false,true,true,false,true,true}).bsd_mitm_allowed); REQUIRE_FALSE(DecideBoot({true,false,true,false,true,true,false}).bsd_mitm_allowed); }

#include <nxless/sys/boot/boot_coordinator.hpp>
#include <nxless/sys/bsd/bsd_mitm_server.hpp>
TEST_CASE("boot coordinator applies admission only for safe transparent mode", "[boot]") {
    nxless::sys::boot::ApplyBsdMitmAdmission(DecideBoot({true,false,true,false,true,true,true}));
    REQUIRE(nxless::sys::bsd::BsdMitmServer::AdmissionEnabled());
    nxless::sys::boot::ApplyBsdMitmAdmission(DecideBoot({true,true,true,false,true,true,true}));
    REQUIRE_FALSE(nxless::sys::bsd::BsdMitmServer::AdmissionEnabled());
}
