#include <nxless/sys/bsd/bsd_mitm_service.hpp>

#if defined(ATMOSPHERE_OS_HORIZON)
namespace nxless::sys::bsd {
namespace {

socket::ClientContextId AllocateContextOrPassthrough() noexcept {
    const auto id = GetClientContextIdAllocator().Allocate();
    return id.value_or(0);
}

} // namespace

BsdMitmService::BsdMitmService(
    std::shared_ptr<::Service>&& forward,
    const ams::sm::MitmProcessInfo& client)
    : MitmServiceImplBase(std::move(forward), client),
      transport_(m_forward_service.get()),
      forwarder_(transport_),
      session_(AllocateContextOrPassthrough(), forwarder_, GetSharedSocketRegistry()) {}

bool BsdMitmService::ShouldMitm(const ams::sm::MitmProcessInfo& client) noexcept {
    return BsdMitmServer::AdmissionEnabled() && client.program_id.value != kNxlessProgramId;
}

ams::Result BsdMitmService::Socket(
    ams::sf::Out<s32> out_ret,
    ams::sf::Out<s32> out_errno,
    const s32 domain,
    const s32 type,
    const s32 protocol) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    const auto result = session_.Socket(domain, type, protocol);
    if (!result.PlatformSucceeded()) {
        return ams::Result(result.platform_result);
    }
    *out_ret = static_cast<s32>(result.bsd.ret);
    *out_errno = result.bsd.bsd_errno;
    R_SUCCEED();
}

ams::Result BsdMitmService::SocketExempt(
    ams::sf::Out<s32> out_ret,
    ams::sf::Out<s32> out_errno,
    const s32 domain,
    const s32 type,
    const s32 protocol) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    const auto result = session_.SocketExempt(domain, type, protocol);
    if (!result.PlatformSucceeded()) {
        return ams::Result(result.platform_result);
    }
    *out_ret = static_cast<s32>(result.bsd.ret);
    *out_errno = result.bsd.bsd_errno;
    R_SUCCEED();
}

ams::Result BsdMitmService::Accept(
    ams::sf::Out<s32> out_ret,
    ams::sf::Out<s32> out_errno,
    ams::sf::Out<u32> out_addrlen,
    const s32 fd,
    ams::sf::OutAutoSelectBuffer address) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    std::uint32_t addrlen = 0;
    const auto result = session_.Accept(
        fd,
        {reinterpret_cast<std::byte*>(address.GetPointer()), address.GetSize()},
        addrlen);
    if (!result.PlatformSucceeded()) {
        return ams::Result(result.platform_result);
    }
    *out_ret = static_cast<s32>(result.bsd.ret);
    *out_errno = result.bsd.bsd_errno;
    *out_addrlen = addrlen;
    R_SUCCEED();
}

ams::Result BsdMitmService::Close(
    ams::sf::Out<s32> out_ret,
    ams::sf::Out<s32> out_errno,
    const s32 fd) noexcept {
    R_UNLESS(!session_.RawPassthroughOnly(), ams::sm::mitm::ResultShouldForwardToSession());
    const auto result = session_.Close(fd);
    if (!result.PlatformSucceeded()) {
        return ams::Result(result.platform_result);
    }
    *out_ret = static_cast<s32>(result.bsd.ret);
    *out_errno = result.bsd.bsd_errno;
    R_SUCCEED();
}

} // namespace nxless::sys::bsd
#endif
