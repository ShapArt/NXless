#pragma once

#include <algorithm>
#include <cstdint>
#include <functional>
#include <random>
#include <utility>
#include <vector>

namespace nxless::test {

class DeterministicExecutor {
public:
    explicit DeterministicExecutor(std::uint32_t seed) : rng_(seed) {}

    template <class Fn>
    void Push(Fn&& fn) {
        actions_.emplace_back(std::forward<Fn>(fn));
    }

    void Run() {
        std::shuffle(actions_.begin(), actions_.end(), rng_);
        for (auto& action : actions_) {
            action();
        }
        actions_.clear();
    }

private:
    std::mt19937 rng_;
    std::vector<std::function<void()>> actions_;
};

} // namespace nxless::test
