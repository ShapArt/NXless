#include <nxless/sys/bsd/bsd_mitm_service.hpp>
#if defined(ATMOSPHERE_OS_HORIZON)
namespace nxless::sys::bsd {
namespace {
socket::ClientContextId AllocateContextOrPassthrough() noexcept {
    const auto id = GetClientContextIdAllocator().Allocate();
    return id.value_or(0);
}
}

BsdMitmService::BsdMitmService(std::shared_ptr<::Service>&& f, const ams::sm::MitmProcessInfo& c)
    : MitmServiceImplBase(std::move(f), c),
      transport_(m_forward_service.get()),
      forwarder_(transport_),
      session_(AllocateContextOrPassthrough(), forwarder_, GetSharedSocketRegistry()) {}

bool BsdMitmService::ShouldMitm(const ams::sm::MitmProcessInfo& c) noexcept {
    return BsdMitmServer::AdmissionEnabled() && c.program_id.value != kNxlessProgramId;
}

ams::Result BsdMitmService::Socket(ams::sf::Out<s32> r, ams::sf::Out<s32> e, s32 d, s32 t, s32 p) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    const auto x = session_.Socket(d, t, p);
    *r = static_cast<s32>(x.ret);
    *e = x.bsd_errno;
    R_SUCCEED();
}

ams::Result BsdMitmService::SocketExempt(ams::sf::Out<s32> r, ams::sf::Out<s32> e, s32 d, s32 t, s32 p) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    const auto x = session_.SocketExempt(d, t, p);
    *r = static_cast<s32>(x.ret);
    *e = x.bsd_errno;
    R_SUCCEED();
}

ams::Result BsdMitmService::Accept(ams::sf::Out<s32> r, ams::sf::Out<s32> e, ams::sf::Out<u32> l, s32 fd,
                                   ams::sf::OutAutoSelectBuffer a) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    std::uint32_t len = 0;
    const auto x = session_.Accept(fd, {reinterpret_cast<std::byte*>(a.GetPointer()), a.GetSize()}, len);
    *r = static_cast<s32>(x.ret);
    *e = x.bsd_errno;
    *l = len;
    R_SUCCEED();
}

ams::Result BsdMitmService::Close(ams::sf::Out<s32> r, ams::sf::Out<s32> e, s32 fd) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    const auto x = session_.Close(fd);
    *r = static_cast<s32>(x.ret);
    *e = x.bsd_errno;
    R_SUCCEED();
}
}
#endif
