#pragma once

#include <cstdint>

#include <nxless/diagnostics/ring_logger.hpp>
#include <nxless/ipc/control_protocol.hpp>
#include <nxless/socket/socket_registry.hpp>

namespace nxless::status {

ipc::RuntimeStatus BuildRuntimeStatus(ipc::RuntimeMode mode,
                                      bool disable_flag_present,
                                      const socket::SocketRegistry& registry,
                                      const diagnostics::RingLogger& logger,
                                      std::int32_t last_internal_error) noexcept;

} // namespace nxless::status
