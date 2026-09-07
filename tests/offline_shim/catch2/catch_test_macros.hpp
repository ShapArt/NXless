#pragma once
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>
namespace nxless_catch_shim {
using Fn = void(*)();
struct Test { const char* name; Fn fn; };
inline std::vector<Test>& tests() { static std::vector<Test> v; return v; }
struct Registrar { Registrar(const char* n, Fn f) { tests().push_back({n,f}); } };
inline void fail(const char* expr, const char* file, int line) {
    throw std::runtime_error(std::string(file)+":"+std::to_string(line)+" REQUIRE("+expr+") failed");
}
}
#define NXLESS_CAT2(a,b) a##b
#define NXLESS_CAT(a,b) NXLESS_CAT2(a,b)
#define TEST_CASE(name, ...) \
    static void NXLESS_CAT(nxless_test_, __LINE__)(); \
    static ::nxless_catch_shim::Registrar NXLESS_CAT(nxless_reg_, __LINE__)(name, &NXLESS_CAT(nxless_test_, __LINE__)); \
    static void NXLESS_CAT(nxless_test_, __LINE__)()
#define REQUIRE(...) do { if (!(__VA_ARGS__)) ::nxless_catch_shim::fail(#__VA_ARGS__, __FILE__, __LINE__); } while(false)
#define REQUIRE_FALSE(...) do { if ((__VA_ARGS__)) ::nxless_catch_shim::fail("!(" #__VA_ARGS__ ")", __FILE__, __LINE__); } while(false)
#define STATIC_REQUIRE(...) static_assert((__VA_ARGS__))
