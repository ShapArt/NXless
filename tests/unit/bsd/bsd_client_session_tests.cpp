#include <array>
#include <cerrno>
#include <cstring>
#include <limits>
#include <catch2/catch_test_macros.hpp>
#include <nxless/socket/client_context_id_allocator.hpp>
#include <nxless/sys/bsd/bsd_client_session.hpp>
#include <nxless/sys/bsd/bsd_mitm_server.hpp>
namespace {
class T final:public nxless::sys::bsd::IOriginalBsdTransport{public:int fd=10;int close_errno=0;std::int32_t Dispatch(const nxless::sys::bsd::IpcDispatch&r) noexcept override{ if(r.command_id==12){struct O{int ret,err;std::uint32_t len;}o{fd++,0,16};std::memcpy(r.output.data(),&o,sizeof(o));}else{struct O{int ret,err;}o{r.command_id==26?(close_errno? -1:0):fd++,r.command_id==26?close_errno:0};std::memcpy(r.output.data(),&o,sizeof(o));}return 0;}};
}
TEST_CASE("context allocator never wraps into a live id", "[bsd_session]"){ nxless::socket::ClientContextIdAllocator a(std::numeric_limits<std::uint64_t>::max()-1); auto x=a.Allocate();auto y=a.Allocate();auto z=a.Allocate(); REQUIRE(x);REQUIRE(y);REQUIRE(*x!=*y);REQUIRE_FALSE(z); }
TEST_CASE("session with exhausted context is explicitly raw passthrough only", "[bsd_session]"){ nxless::socket::SocketRegistry reg; T t; nxless::sys::bsd::BsdForwarder f(t); nxless::sys::bsd::BsdClientSession s(0,f,reg); REQUIRE_FALSE(s.RegistryAttached()); REQUIRE(s.RawPassthroughOnly()); REQUIRE(reg.ActiveClientCount()==0); }
TEST_CASE("session owns socket accept close and teardown registry state", "[bsd_session]"){ nxless::socket::SocketRegistry reg; T t; nxless::sys::bsd::BsdForwarder f(t); { nxless::sys::bsd::BsdClientSession s(77,f,reg); REQUIRE(s.RegistryAttached()); auto a=s.Socket(2,1,6); REQUIRE(a.ret==10); REQUIRE(reg.Find(77,10)); std::array<std::byte,32> addr{};std::uint32_t len=0; auto b=s.Accept(10,addr,len); REQUIRE(b.ret==11); REQUIRE(reg.Find(77,11)); t.close_errno=EBADF; REQUIRE(s.Close(10).bsd_errno==EBADF); REQUIRE_FALSE(reg.Find(77,10)); REQUIRE(reg.ActiveClientCount()==1); } REQUIRE(reg.ActiveClientCount()==0); REQUIRE(reg.ActiveSocketCount()==0); }
#if defined(NXLESS_ENABLE_PHASE0_TEST_HOOKS)
TEST_CASE("development proxy candidate marker changes only registry tag", "[bsd_session]"){ nxless::socket::SocketRegistry reg;T t;nxless::sys::bsd::BsdForwarder f(t);nxless::sys::bsd::BsdClientSession s(88,f,reg);auto x=s.Socket(2,1,6);REQUIRE(x.ret>=0);REQUIRE(s.MarkProxyCandidateForTest(static_cast<int>(x.ret)));REQUIRE(reg.Find(88,static_cast<int>(x.ret))->tag==nxless::socket::InterceptionTag::ProxyCandidate); }
#endif

TEST_CASE("mitm admission follows safe boot decision", "[bsd_session]") {
    nxless::sys::bsd::BsdMitmServer::SetAdmissionEnabled(false);
    REQUIRE_FALSE(nxless::sys::bsd::BsdMitmServer::AdmissionEnabled());
    nxless::sys::bsd::BsdMitmServer::SetAdmissionEnabled(true);
    REQUIRE(nxless::sys::bsd::BsdMitmServer::AdmissionEnabled());
    nxless::sys::bsd::BsdMitmServer::SetAdmissionEnabled(false);
}
