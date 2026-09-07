# NXless Phase 0 config v1

Phase 0 intentionally accepts only a tiny strict configuration surface.

```toml
version = 1
diagnostics_enabled = true
```

Limits: the file is at most 64 KiB; each line is at most 1024 bytes; duplicate keys, unknown keys, invalid booleans, unsupported versions, NUL bytes, and non-ASCII key names are rejected. A rejected configuration produces safe defaults and never enables interception by itself. Missing-file handling belongs to the Horizon SD config adapter, not this parser.
