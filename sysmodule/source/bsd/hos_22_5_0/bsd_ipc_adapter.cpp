#include <nxless/sys/bsd/hos_22_5_0/bsd_ipc_adapter.hpp>

#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere/sf/sf_mitm_dispatch.h>

namespace nxless::sys::bsd::hos_22_5_0 {

std::uint32_t HorizonOriginalBsdTransport::Dispatch(const IpcDispatch& request) noexcept {
    if (forward_ == nullptr || request.buffer_count > kMaxHipcBuffers ||
        !FitsHipcU32(request.input.size()) || !FitsHipcU32(request.output.size())) {
        return ams::sf::ResultNotSupported().GetValue();
    }

    SfMitmDispatchParams params{};
    for (std::size_t index = 0; index < request.buffer_count; ++index) {
        const auto& buffer = request.buffers[index];
        if (!FitsHipcU32(buffer.size)) {
            return ams::sf::ResultNotSupported().GetValue();
        }

        const u32 direction = buffer.direction == IpcBufferDirection::In
                                  ? SfBufferAttr_In
                              : buffer.direction == IpcBufferDirection::Out
                                  ? SfBufferAttr_Out
                                  : (SfBufferAttr_In | SfBufferAttr_Out);
        const u32 attributes = direction | SfBufferAttr_HipcAutoSelect;

        switch (index) {
            case 0: params.buffer_attrs.attr0 = attributes; break;
            case 1: params.buffer_attrs.attr1 = attributes; break;
            case 2: params.buffer_attrs.attr2 = attributes; break;
            case 3: params.buffer_attrs.attr3 = attributes; break;
            case 4: params.buffer_attrs.attr4 = attributes; break;
            case 5: params.buffer_attrs.attr5 = attributes; break;
            case 6: params.buffer_attrs.attr6 = attributes; break;
            case 7: params.buffer_attrs.attr7 = attributes; break;
            default: return ams::sf::ResultNotSupported().GetValue();
        }
        params.buffers[index] = {buffer.data, buffer.size};
    }

    const ams::Result result = serviceMitmDispatchImpl(
        forward_,
        request.command_id,
        request.input.data(),
        static_cast<u32>(request.input.size()),
        request.output.data(),
        static_cast<u32>(request.output.size()),
        params);
    return result.GetValue();
}

} // namespace nxless::sys::bsd::hos_22_5_0
#endif
