#pragma once
#include <atomic>
#include <cstdint>
#include <limits>
#include <optional>
#include <nxless/socket/socket_key.hpp>
namespace nxless::socket {
class ClientContextIdAllocator {
public:
    explicit constexpr ClientContextIdAllocator(ClientContextId first=1) noexcept : next_(first==0?1:first) {}
    std::optional<ClientContextId> Allocate() noexcept {
        ClientContextId current=next_.load(std::memory_order_relaxed);
        while(current!=0){
            const ClientContextId desired=current==std::numeric_limits<ClientContextId>::max()?0:current+1;
            if(next_.compare_exchange_weak(current,desired,std::memory_order_relaxed,std::memory_order_relaxed)) return current;
        }
        return std::nullopt;
    }
private:
    std::atomic<ClientContextId> next_;
};
}
