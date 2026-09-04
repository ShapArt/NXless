#pragma once
#include <nxless/sys/bsd/bsd_forwarder.hpp>
#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere.hpp>
namespace nxless::sys::bsd::hos_22_5_0 {
class HorizonOriginalBsdTransport final : public IOriginalBsdTransport {
public: explicit HorizonOriginalBsdTransport(Service* forward) noexcept : forward_(forward) {}
    std::int32_t Dispatch(const IpcDispatch& request) noexcept override;
private: Service* forward_{};
};
}
#endif
