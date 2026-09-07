#pragma once
#include <switch.h>

namespace ams::fs {
struct ResultPathNotFound {
    static bool Includes(::Result result);
};
}
