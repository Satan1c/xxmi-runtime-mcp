# XXMI Runtime MCP

A local MCP companion for testing XXMI mods and DLL builds. Use it with a stock
SpectrumQT release or with the optional telemetry patch for a Satan1c dev build.

## Setup

1. Install Python 3.11 or newer and run `python -m pip install -r requirements.txt`
   in a virtual environment.
2. Set `log_level = info` and `unbuffered = 1` in `[Logging]` so
   `d3d11_log.txt` includes current `[Hunting]` registrations and results.
   Keep these settings consistent when comparing performance across builds. Start the game with hunting enabled (`hunting = 1`)
   when testing dumps or hunting.
3. Focus the game and get its window ID. On CachyOS install `xdotool` and use
   `xdotool getactivewindow` with the game focused. Run the MCP on the same
   desktop session. The Linux backend uses X11/XWayland, including Proton games
   running through XWayland. Native Wayland input needs a different backend.
   On Windows, use the game's window handle, for example the
   `MainWindowHandle` from PowerShell's `Get-Process`.
4. Configure your MCP client to launch the virtual environment's Python with
   these arguments. Use the directory containing the loaded `d3d11.dll`,
   its log and its frame analysis output for `--dll-root`.

```json
{
  "mcpServers": {
    "xxmi-runtime": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/xxmi-runtime-mcp/server.py", "--dll-root", "/path/to/game", "--window", "12345"]
    }
  }
}
```

Omit `--window` for read-only tools. Update the window ID after a relaunch if
it changes. Input requires that window to be foreground and can affect gameplay.
Keep modifier and keypad keys released before testing. Unsupported key names,
controller bindings, and mouse buttons require another binding or input backend.

## Workflow

- Call `get_bindings` to see the bindings XXMI registered for hunting and
  profiling. It uses the latest logged `[Hunting]` section, so bindings
  reflect the DLL's include and override behavior. Reload the configuration
  after editing it. There is no fallback to F8 or other defaults.
- Use `run_action` for next, previous, mark, or profiling actions and
  `press_key` for an explicit XXMI-style keyboard chord. The default press
  lasts 100 ms so a polling game can observe it. Keep Num Lock on for keypad
  digit bindings. Set `hold_ms` for frame analysis configured with `hold`.
- Use `trigger_dump` for frame analysis. It returns a local path when XXMI
  logs completion and a new output directory exists. An unconfirmed result
  can include directories created during the attempt. Use `list_dumps`
  and `search_hash` to inspect recorded files.
- Stock DLLs can log marked shader and buffer hashes. Marking runs the configured
  `marking_actions`, which may write shader files or change the clipboard.
  Enable the performance monitor, let it sample, then freeze it to capture FPS
  in the log. `get_runtime_state` shows the most recent logged values.
- Dev DLLs patched with the adapter additionally log changed hunting selections
  and the profiling overlay text. See [adapter maintenance](https://github.com/Satan1c/xxmi-runtime-mcp/tree/dev/satan1c/adapters).
- Install the bundled [agent skill](skills/xxmi-runtime/SKILL.md) in your
  MCP client's skills directory to give the agent this workflow.

Run the companion tests with `python -m unittest -v`. A live acceptance run should
remap the dump hotkey via an include, reload, verify the new reported binding,
capture a dump, search for a known hash, step a shader, and sample profiling.
Repeat on stock Windows and Steam/Proton XWayland before cutting a release.
