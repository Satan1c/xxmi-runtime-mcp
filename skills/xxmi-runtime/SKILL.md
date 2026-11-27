---
name: xxmi-runtime
description: Use the local XXMI Runtime MCP to send game hotkeys, test mods, capture frame-analysis dumps, hunt shader or buffer hashes, and read XXMI profiling on Windows or Linux/Proton.
---

1. Call `get_bindings` before using a named action. XXMI's latest registration
   log is the source for the loaded keys. Ask the user to reload or restart
   if they edited a binding and it still shows the previous value.
2. Use `run_action` for hunting and profiling controls. Read
   `get_runtime_state` after a step when the DLL has the telemetry adapter.
   On stock builds, marking can return the logged hash. Mark only when the
   configured marking side effects are appropriate for the task.
3. Use `trigger_dump` and report its completion status and returned path.
   For an unconfirmed capture, inspect `list_dumps`. Use `search_hash` for
   exact 8- or 16-digit hashes within a dump.
4. For stock profiling, turn on the monitor, allow it to collect samples,
   then freeze it and read the logged FPS. For adapter builds report the
   latest overlay snapshot and whether it has the requested metrics.
5. If focus is refused, ask the user to focus the configured game window.
   If a keyboard binding cannot be translated, report the token that failed.
