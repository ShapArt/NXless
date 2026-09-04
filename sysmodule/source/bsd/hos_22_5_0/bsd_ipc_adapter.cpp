#include <nxless/sys/bsd/hos_22_5_0/bsd_ipc_adapter.hpp>
#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere/sf/sf_mitm_dispatch.h>
namespace nxless::sys::bsd::hos_22_5_0 {
std::int32_t HorizonOriginalBsdTransport::Dispatch(const IpcDispatch& r) noexcept {
    if(forward_==nullptr || r.buffer_count>kMaxHipcBuffers || !FitsHipcU32(r.input.size()) || !FitsHipcU32(r.output.size())) return -1;
    SfMitmDispatchParams p{}; for(std::size_t i=0;i<r.buffer_count;++i){ const auto& b=r.buffers[i]; if(!FitsHipcU32(b.size)) return -1;
        const u32 dir=b.direction==IpcBufferDirection::In ? SfBufferAttr_In : b.direction==IpcBufferDirection::Out ? SfBufferAttr_Out : (SfBufferAttr_In|SfBufferAttr_Out);
        const u32 attr=dir|SfBufferAttr_HipcAutoSelect;
        switch(i){ case 0:p.buffer_attrs.attr0=attr;break; case 1:p.buffer_attrs.attr1=attr;break; case 2:p.buffer_attrs.attr2=attr;break; case 3:p.buffer_attrs.attr3=attr;break; case 4:p.buffer_attrs.attr4=attr;break; case 5:p.buffer_attrs.attr5=attr;break; case 6:p.buffer_attrs.attr6=attr;break; case 7:p.buffer_attrs.attr7=attr;break; default:return -1; }
        p.buffers[i]={b.data,b.size}; }
    const ams::Result rc=serviceMitmDispatchImpl(forward_,r.command_id,r.input.data(),static_cast<u32>(r.input.size()),r.output.data(),static_cast<u32>(r.output.size()),p);
    return static_cast<std::int32_t>(rc.GetValue());
}
}
#endif
