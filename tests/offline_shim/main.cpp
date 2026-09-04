#include <catch2/catch_test_macros.hpp>
#include <cstdio>
#include <exception>
int main() {
    int failed = 0;
    for (const auto& t : nxless_catch_shim::tests()) {
        try { t.fn(); }
        catch (const std::exception& e) { ++failed; std::fprintf(stderr, "FAIL: %s: %s\n", t.name, e.what()); }
        catch (...) { ++failed; std::fprintf(stderr, "FAIL: %s: unknown exception\n", t.name); }
    }
    std::printf("offline-shim tests: %zu total, %d failed\n", nxless_catch_shim::tests().size(), failed);
    return failed == 0 ? 0 : 1;
}
