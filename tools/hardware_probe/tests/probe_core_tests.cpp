#include <cassert>
#include <cstring>
#include <string_view>

#include <nxless/probe/probe_core.hpp>

int main() {
    using namespace nxless::probe;
    ProbeConfig cfg{};
    assert(ParseConfigText("host=192.168.1.20\ntcp_port=5001\nudp_port=5002\nconcurrent=4\n", cfg));
    assert(std::strcmp(cfg.host.data(), "192.168.1.20") == 0);
    assert(cfg.tcp_port == 5001);
    assert(cfg.udp_port == 5002);
    assert(cfg.concurrent == 4);

    assert(!ParseConfigText("host=example.com\n", cfg));
    assert(!ParseConfigText("host=192.168.1.20\nconcurrent=17\n", cfg));
    assert(!ParseConfigText("host=999.1.1.1\n", cfg));
    assert(!ParseConfigText("host=192.168.1.20\ntcp_port=0\n", cfg));

    assert(std::string_view(RuntimeModeName(nxless::ipc::RuntimeMode::SafeDisabled)) == "SafeDisabled");
    assert(std::string_view(RuntimeModeName(nxless::ipc::RuntimeMode::DisconnectedPassthrough)) == "DisconnectedPassthrough");
    assert(std::string_view(RuntimeModeName(nxless::ipc::RuntimeMode::UnsupportedHos)) == "UnsupportedHos");
    assert(std::string_view(RuntimeModeName(nxless::ipc::RuntimeMode::ErrorPassthrough)) == "ErrorPassthrough");
    return 0;
}
