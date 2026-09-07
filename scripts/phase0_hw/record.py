from .schema import (
    ATMOSPHERE_VERSION, ATMOSPHERE_COMMIT, LIBNX_VERSION, LIBNX_COMMIT, DEVKITA64, HOS, PROGRAM_ID, REQUIRED_COUNTS,
    _git, sha256_file, new_record as _schema_new_record, append_boot, add_lifecycle_attempt,
)
from .validate import validate_record
from .report import render_markdown, synthetic_complete_record as _report_synthetic_complete_record
from .registry_telemetry import initialize_registry_telemetry, bind_synthetic_registry_telemetry


def new_record(repo_root):
    return initialize_registry_telemetry(_schema_new_record(repo_root))


def synthetic_complete_record():
    return bind_synthetic_registry_telemetry(_report_synthetic_complete_record())


__all__ = [
    "ATMOSPHERE_VERSION", "ATMOSPHERE_COMMIT", "LIBNX_VERSION", "LIBNX_COMMIT", "DEVKITA64", "HOS", "PROGRAM_ID", "REQUIRED_COUNTS",
    "_git", "sha256_file", "new_record", "append_boot", "add_lifecycle_attempt", "validate_record", "render_markdown", "synthetic_complete_record",
]
