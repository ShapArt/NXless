#include <nxless/diagnostics/ring_logger.hpp>
#include <nxless/ipc/control_runtime.hpp>
#include <nxless/ipc/control_state.hpp>
#include <nxless/sys/boot/boot_coordinator.hpp>
#include <nxless/sys/bsd/bsd_mitm_server.hpp>
#include <nxless/sys/config/sd_config_store.hpp>
#include <nxless/sys/ipc/control_service.hpp>
#include <nxless/sys/platform/compatibility.hpp>

#if defined(ATMOSPHERE_OS_HORIZON)
#include <stratosphere.hpp>

namespace ams {
namespace {

constexpr std::size_t kMallocBufferSize = 2_MB;
alignas(os::MemoryPageSize) constinit u8 g_malloc_buffer[kMallocBufferSize];

constinit bool g_sm_ready = false;
constinit bool g_fs_ready = false;
constinit bool g_sd_fs_open = false;
constinit FsFileSystem g_sd_fs{};
constinit nxless::sys::config::SdConfigStore g_sd_config_store{};
constinit nxless::ipc::ControlState g_control_state{};
constinit bool g_disable_flag_present = false;
constinit nxless::sys::platform::HosVersion g_hos{};

nxless::sys::config::SdConfigStore& GetSdConfigStore() noexcept {
    return g_sd_config_store;
}

nxless::diagnostics::RingLogger& GetLogger() noexcept {
    static nxless::diagnostics::RingLogger logger;
    return logger;
}

nxless::ipc::ControlRuntime& GetControlRuntime() noexcept {
    static nxless::ipc::ControlRuntime runtime(nxless::sys::bsd::GetSharedSocketRegistry(), GetLogger());
    return runtime;
}

struct ControlManagerOptions {
    static constexpr std::size_t PointerBufferSize = 0x400;
    static constexpr std::size_t MaxDomains = 0;
    static constexpr std::size_t MaxDomainObjects = 0;
    static constexpr bool CanDeferInvokeRequest = false;
    static constexpr bool CanManageMitmServers = false;
};

constexpr std::size_t kControlMaxSessions = 2;
using ControlManager = sf::hipc::ServerManager<1, ControlManagerOptions, kControlMaxSessions>;

ControlManager& GetControlManager() noexcept {
    static ControlManager manager;
    return manager;
}

constexpr std::size_t kControlThreadStackSize = 0x4000;
alignas(os::MemoryPageSize) constinit u8 g_control_thread_stack[kControlThreadStackSize];
constinit os::ThreadType g_control_thread{};

void ControlThreadMain(void*) {
    GetControlManager().LoopProcess();
}

void NORETURN IdleFailOpen() noexcept {
    while (true) {
        svc::SleepThread(TimeSpan::FromSeconds(30).GetNanoSeconds());
    }
}

bool StartControlService() noexcept {
    constexpr s32 kControlThreadPriority = 32;
    const Result thread_rc = os::CreateThread(
        &g_control_thread,
        ControlThreadMain,
        nullptr,
        g_control_thread_stack,
        sizeof(g_control_thread_stack),
        kControlThreadPriority);
    if (R_FAILED(thread_rc)) {
        g_control_state.SetLastInternalError(static_cast<std::int32_t>(thread_rc.GetValue()));
        return false;
    }

    auto service = sf::CreateSharedObjectEmplaced<nxless::sys::ipc::IControlService, nxless::sys::ipc::ControlService>(
        GetControlRuntime(), g_control_state, g_disable_flag_present, g_hos);
    if (service == nullptr) {
        constexpr std::int32_t kControlObjectAllocationFailed = -1;
        g_control_state.SetLastInternalError(kControlObjectAllocationFailed);
        os::DestroyThread(&g_control_thread);
        return false;
    }

    constexpr sm::ServiceName service_name = sm::ServiceName::Encode("nxl:ctl");
    const Result register_rc = GetControlManager().RegisterObjectForServer(
        std::move(service), service_name, kControlMaxSessions);
    if (R_FAILED(register_rc)) {
        g_control_state.SetLastInternalError(static_cast<std::int32_t>(register_rc.GetValue()));
        os::DestroyThread(&g_control_thread);
        return false;
    }

    os::SetThreadNamePointer(&g_control_thread, "nxless::Control");
    os::StartThread(&g_control_thread);
    return true;
}

} // namespace

namespace init {

void InitializeSystemModule() {
    const Result sm_rc = sm::Initialize();
    g_sm_ready = R_SUCCEEDED(sm_rc);
    if (!g_sm_ready) {
        g_control_state.SetLastInternalError(static_cast<std::int32_t>(sm_rc.GetValue()));
        return;
    }

}

void FinalizeSystemModule() {
    if (g_sd_fs_open) {
        fsFsClose(&g_sd_fs);
        g_sd_fs_open = false;
    }
    if (g_fs_ready) {
        fsExit();
        g_fs_ready = false;
    }
    if (g_sm_ready) {
        static_cast<void>(sm::Finalize());
        g_sm_ready = false;
    }
}

void Startup() {
    init::InitializeAllocator(g_malloc_buffer, sizeof(g_malloc_buffer));
}

} // namespace init

void NORETURN Exit(int rc) {
    AMS_UNUSED(rc);
    IdleFailOpen();
}

void Main() {
    if (!g_sm_ready) {
        IdleFailOpen();
    }

    const ::Result fs_rc = fsInitialize();
    g_fs_ready = R_SUCCEEDED(fs_rc);
    if (!g_fs_ready) {
        g_control_state.SetLastInternalError(static_cast<std::int32_t>(fs_rc));
    }

    if (g_fs_ready) {
        const ::Result sd_rc = fsOpenSdCardFileSystem(&g_sd_fs);
        g_sd_fs_open = R_SUCCEEDED(sd_rc);
        if (!g_sd_fs_open) {
            g_control_state.SetLastInternalError(static_cast<std::int32_t>(sd_rc));
        }
    }

    nxless::sys::config::SdLoadResult sd{};
    if (g_sd_fs_open) {
        sd = GetSdConfigStore().Load(&g_sd_fs);
        fsFsClose(&g_sd_fs);
        g_sd_fs_open = false;
    }
    if (g_fs_ready) {
        fsExit();
        g_fs_ready = false;
    }

    g_hos = nxless::sys::platform::QueryHosVersion();
    g_disable_flag_present = sd.disable_flag_present;

    const nxless::status::BootDecision pre_control_decision = nxless::sys::boot::BuildBootDecision(sd, g_hos, true);
    g_control_state.SetMode(pre_control_decision.mode);

    const bool control_available = StartControlService();
    const nxless::status::BootDecision decision = nxless::sys::boot::BuildBootDecision(sd, g_hos, control_available);
    g_control_state.SetMode(decision.mode);
    nxless::sys::boot::ApplyBsdMitmAdmission(decision);

    if (!control_available || !decision.bsd_mitm_allowed) {
        IdleFailOpen();
    }

    static nxless::sys::bsd::HorizonBsdMitmServer bsd_manager;
    const Result register_rc = bsd_manager.RegisterIfAllowed(true);
    if (R_FAILED(register_rc)) {
        g_control_state.Store(
            nxless::ipc::RuntimeMode::ErrorPassthrough,
            static_cast<std::int32_t>(register_rc.GetValue()));
        nxless::sys::bsd::BsdMitmServer::SetAdmissionEnabled(false);
        IdleFailOpen();
    }

    bsd_manager.LoopProcess();
    IdleFailOpen();
}

} // namespace ams
#endif
