#include <switch.h>

#include <arpa/inet.h>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

#include <nxless/ipc/control_protocol.hpp>
#include <nxless/probe/probe_core.hpp>

namespace {

constexpr const char* kConfigPath = "sdmc:/switch/NXlessProbe/probe.ini";
constexpr std::size_t kConfigMaxBytes = 1024;
constexpr std::size_t kPayloadMax = 64;
constexpr int kIoTimeoutSeconds = 5;

bool LoadProbeConfig(nxless::probe::ProbeConfig& config) noexcept {
    FILE* file = std::fopen(kConfigPath, "rb");
    if (file == nullptr) {
        std::printf("Config missing: %s\n", kConfigPath);
        return false;
    }
    std::array<char, kConfigMaxBytes + 1> buffer{};
    const std::size_t size = std::fread(buffer.data(), 1, kConfigMaxBytes + 1, file);
    std::fclose(file);
    if (size == 0 || size > kConfigMaxBytes) {
        std::printf("Config invalid/too large (max %zu bytes)\n", kConfigMaxBytes);
        return false;
    }
    return nxless::probe::ParseConfigText(std::string_view(buffer.data(), size), config);
}

void SetSocketTimeout(const int fd) noexcept {
    timeval timeout{};
    timeout.tv_sec = kIoTimeoutSeconds;
    timeout.tv_usec = 0;
    static_cast<void>(setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)));
    static_cast<void>(setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)));
}

bool FillAddress(const nxless::probe::ProbeConfig& config, const std::uint16_t port, sockaddr_in& out) noexcept {
    out = {};
    out.sin_family = AF_INET;
    out.sin_port = htons(port);
    return inet_pton(AF_INET, config.host.data(), &out.sin_addr) == 1;
}

bool SendAll(const int fd, const char* data, const std::size_t size) noexcept {
    std::size_t sent = 0;
    while (sent < size) {
        const ssize_t n = send(fd, data + sent, size - sent, 0);
        if (n <= 0) {
            return false;
        }
        sent += static_cast<std::size_t>(n);
    }
    return true;
}

bool RecvAll(const int fd, char* data, const std::size_t size) noexcept {
    std::size_t received = 0;
    while (received < size) {
        const ssize_t n = recv(fd, data + received, size - received, 0);
        if (n <= 0) {
            return false;
        }
        received += static_cast<std::size_t>(n);
    }
    return true;
}

bool RunTcpEcho(const nxless::probe::ProbeConfig& config) noexcept {
    sockaddr_in address{};
    if (!FillAddress(config, config.tcp_port, address)) {
        return false;
    }
    std::array<int, 16> sockets{};
    sockets.fill(-1);
    bool ok = true;
    for (std::uint32_t i = 0; i < config.concurrent; ++i) {
        sockets[i] = socket(AF_INET, SOCK_STREAM, 0);
        if (sockets[i] < 0) {
            ok = false;
            break;
        }
        SetSocketTimeout(sockets[i]);
        if (connect(sockets[i], reinterpret_cast<const sockaddr*>(&address), sizeof(address)) != 0) {
            ok = false;
            break;
        }
    }

    for (std::uint32_t i = 0; ok && i < config.concurrent; ++i) {
        std::array<char, kPayloadMax> payload{};
        const int length = std::snprintf(payload.data(), payload.size(), "NXLESS_TCP_%u", i);
        if (length <= 0 || static_cast<std::size_t>(length) >= payload.size()) {
            ok = false;
            break;
        }
        std::array<char, kPayloadMax> reply{};
        const auto size = static_cast<std::size_t>(length);
        ok = SendAll(sockets[i], payload.data(), size) && RecvAll(sockets[i], reply.data(), size) &&
             std::memcmp(payload.data(), reply.data(), size) == 0;
    }

    for (const int fd : sockets) {
        if (fd >= 0) {
            close(fd);
        }
    }
    return ok;
}

bool RunUdpEcho(const nxless::probe::ProbeConfig& config) noexcept {
    sockaddr_in address{};
    if (!FillAddress(config, config.udp_port, address)) {
        return false;
    }
    std::array<int, 16> sockets{};
    sockets.fill(-1);
    bool ok = true;
    for (std::uint32_t i = 0; i < config.concurrent; ++i) {
        sockets[i] = socket(AF_INET, SOCK_DGRAM, 0);
        if (sockets[i] < 0) {
            ok = false;
            break;
        }
        SetSocketTimeout(sockets[i]);
    }

    for (std::uint32_t i = 0; ok && i < config.concurrent; ++i) {
        std::array<char, kPayloadMax> payload{};
        const int length = std::snprintf(payload.data(), payload.size(), "NXLESS_UDP_%u", i);
        if (length <= 0 || static_cast<std::size_t>(length) >= payload.size()) {
            ok = false;
            break;
        }
        const auto size = static_cast<std::size_t>(length);
        const ssize_t sent = sendto(sockets[i], payload.data(), size, 0,
                                    reinterpret_cast<const sockaddr*>(&address), sizeof(address));
        if (sent != static_cast<ssize_t>(size)) {
            ok = false;
            break;
        }
        std::array<char, kPayloadMax> reply{};
        sockaddr_in source{};
        socklen_t source_len = sizeof(source);
        const ssize_t received = recvfrom(sockets[i], reply.data(), reply.size(), 0,
                                          reinterpret_cast<sockaddr*>(&source), &source_len);
        ok = received == static_cast<ssize_t>(size) && std::memcmp(payload.data(), reply.data(), size) == 0;
    }

    for (const int fd : sockets) {
        if (fd >= 0) {
            close(fd);
        }
    }
    return ok;
}

enum class ControlProbeState {
    Unavailable,
    Error,
    Available,
};

const char* ControlProbeStateName(const ControlProbeState state) noexcept {
    switch (state) {
        case ControlProbeState::Unavailable:
            return "UNAVAILABLE";
        case ControlProbeState::Error:
            return "ERROR";
        case ControlProbeState::Available:
            return "PASS";
    }
    return "ERROR";
}

ControlProbeState QueryControl(nxless::ipc::VersionInfo& version,
                               nxless::ipc::CompatibilityInfo& compatibility,
                               nxless::ipc::RuntimeStatus& status) noexcept {
    Service ctl{};
    Result rc = smGetService(&ctl, "nxl:ctl");
    if (R_FAILED(rc)) {
        std::printf("nxl:ctl unavailable: 0x%08X\n", rc);
        return ControlProbeState::Unavailable;
    }
    rc = serviceDispatchOut(&ctl, 0, version);
    if (R_SUCCEEDED(rc)) {
        rc = serviceDispatchOut(&ctl, 1, compatibility);
    }
    if (R_SUCCEEDED(rc)) {
        rc = serviceDispatchOut(&ctl, 2, status);
    }
    serviceClose(&ctl);
    if (R_FAILED(rc)) {
        std::printf("nxl:ctl query failed: 0x%08X\n", rc);
        return ControlProbeState::Error;
    }
    return ControlProbeState::Available;
}

void PrintStatus(const nxless::ipc::VersionInfo& version,
                 const nxless::ipc::CompatibilityInfo& compatibility,
                 const nxless::ipc::RuntimeStatus& status) noexcept {
    std::printf("nxl:ctl API %u.%u\n", version.api_major, version.api_minor);
    std::printf("HOS %u.%u.%u, bsd_mitm_supported=%u\n",
                compatibility.hos_major, compatibility.hos_minor, compatibility.hos_patch,
                compatibility.bsd_mitm_supported);
    std::printf("mode=%s disable.flag=%u\n", nxless::probe::RuntimeModeName(status.mode), status.disable_flag_present);
    std::printf("clients=%u client-high-water=%u sockets=%u socket-high-water=%u dropped-logs=%llu last-error=%d\n",
                status.active_clients, status.client_high_water, status.active_sockets, status.socket_high_water,
                static_cast<unsigned long long>(status.log_dropped), status.last_internal_error);
}

} // namespace

int main(int, char**) {
    consoleInit(nullptr);
    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad{};
    padInitializeDefault(&pad);

    std::printf("NXless Phase 0 Hardware Probe\n");
    std::printf("Test-only NRO; never ship in the NXless release ZIP.\n\n");

    nxless::probe::ProbeConfig config{};
    const bool config_ok = LoadProbeConfig(config);
    if (!config_ok) {
        std::printf("Expected config:\n  host=192.168.1.10\n  tcp_port=5001\n  udp_port=5002\n  concurrent=4\n\n");
    } else {
        std::printf("Echo target %s TCP:%u UDP:%u concurrency:%u\n",
                    config.host.data(), config.tcp_port, config.udp_port, config.concurrent);
    }

    nxless::ipc::VersionInfo version{};
    nxless::ipc::CompatibilityInfo compatibility{};
    nxless::ipc::RuntimeStatus status{};
    const ControlProbeState ctl_state_before = QueryControl(version, compatibility, status);
    if (ctl_state_before == ControlProbeState::Available) {
        PrintStatus(version, compatibility, status);
    }

    bool tcp_ok = false;
    bool udp_ok = false;
    if (config_ok) {
        const Result socket_rc = socketInitializeDefault();
        if (R_FAILED(socket_rc)) {
            std::printf("socketInitializeDefault failed: 0x%08X\n", socket_rc);
        } else {
            tcp_ok = RunTcpEcho(config);
            std::printf("TCP echo: %s\n", tcp_ok ? "PASS" : "FAIL");
            udp_ok = RunUdpEcho(config);
            std::printf("UDP echo: %s\n", udp_ok ? "PASS" : "FAIL");

            nxless::ipc::VersionInfo after_version{};
            nxless::ipc::CompatibilityInfo after_compatibility{};
            nxless::ipc::RuntimeStatus after_status{};
            if (QueryControl(after_version, after_compatibility, after_status) == ControlProbeState::Available) {
                std::printf("\nStatus after socket tests:\n");
                PrintStatus(after_version, after_compatibility, after_status);
            }
            socketExit();
        }
    }

    std::printf("\nSummary: ctl=%s tcp=%s udp=%s\n",
                ControlProbeStateName(ctl_state_before),
                tcp_ok ? "PASS" : "FAIL",
                udp_ok ? "PASS" : "FAIL");
    std::printf("Press + to return to HBMenu.\n");

    while (appletMainLoop()) {
        padUpdate(&pad);
        if ((padGetButtonsDown(&pad) & HidNpadButton_Plus) != 0) {
            break;
        }
        consoleUpdate(nullptr);
    }
    consoleExit(nullptr);
    return 0;
}
