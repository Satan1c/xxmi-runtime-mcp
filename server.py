"""Local stdio MCP for a single XXMI installation."""
import argparse
from pathlib import Path
from threading import Lock
import time

from mcp.server.fastmcp import FastMCP

from input_keys import press
from runtime import (
    ACTIONS, HUNT_STEP_KINDS, bindings, completed_dump, decode, dump_dirs,
    frozen_fps, hashes, hunt_result,
    marked_hash, performance, selection,
)


def create_server(root, window):
    server = FastMCP("xxmi-runtime")
    lock = Lock()
    log = root / "d3d11_log.txt"

    def read_log(offset=0):
        with log.open("rb") as stream:
            stream.seek(offset)
            return decode(stream.read()).replace("\r\n", "\n")

    def send(action, hold_ms):
        binding = bindings(read_log()).get(action)
        if not binding:
            raise ValueError(f"No registered keyboard binding for {action}")
        press(binding, window, hold_ms)
        return binding

    @server.tool()
    def get_bindings() -> dict:
        """List the current hunting and profiling bindings registered in the XXMI log."""
        return bindings(read_log())

    @server.tool()
    def press_key(binding: str, hold_ms: int = 100) -> dict:
        """Send one XXMI-style keyboard chord to the configured focused game window."""
        with lock:
            press(binding, window, max(25, min(hold_ms, 2000)))
        return {"sent": binding}

    @server.tool()
    def run_action(action: str) -> dict:
        """Send a registered hunting or profiling action. Use trigger_dump for frame analysis."""
        if action not in ACTIONS - {"analyse_frame"}:
            raise ValueError("Unknown action. See get_bindings.")
        with lock:
            offset = log.stat().st_size
            key = send(action, 100)
            if action.startswith("mark_") or action == "freeze_performance_monitor":
                time.sleep(0.2)
            fresh = read_log(offset)
            return {"action": action, "sent": key, "marked": marked_hash(fresh),
                    "selected_hashes": selection(fresh), "frozen_fps": frozen_fps(fresh)}

    @server.tool()
    def hunt_step(kind: str, direction: str = "next", timeout_seconds: float = 3) -> dict:
        """Step a shader or buffer and wait for the patched DLL's selected hash.

        Use kinds such as pixelshader, vertexshader, indexbuffer, or vertexbuffer.
        """
        if kind not in HUNT_STEP_KINDS or direction not in {"next", "previous"}:
            raise ValueError("Expected a shader or buffer kind and next or previous")
        action = f"{direction}_{kind}"

        with lock:
            offset = log.stat().st_size
            key = send(action, 80)
            deadline = time.monotonic() + max(0, min(timeout_seconds, 15))
            while True:
                result = hunt_result(read_log(offset), action)
                if result is not None:
                    return {"action": action, "sent": key, "status": "confirmed", **result}
                if time.monotonic() >= deadline:
                    return {"action": action, "sent": key, "status": "unconfirmed"}
                time.sleep(0.05)

    @server.tool()
    def trigger_dump(hold_ms: int = 100, timeout_seconds: float = 15) -> dict:
        """Trigger the registered frame analysis hotkey and return observed output paths."""
        with lock:
            existing = dump_dirs(root)
            offset = log.stat().st_size
            key = send("analyse_frame", max(25, min(hold_ms, 2000)))
            deadline = time.monotonic() + max(0, min(timeout_seconds, 120))
            while True:
                new = {name: path for name, path in dump_dirs(root).items()
                       if name not in existing}
                path = completed_dump(read_log(offset), new)
                if path:
                    return {"sent": key, "status": "saved", "path": path}
                if time.monotonic() >= deadline:
                    return {"sent": key, "status": "unconfirmed",
                            "observed_directories": [str(path) for path in new.values()]}
                time.sleep(0.2)

    @server.tool()
    def list_dumps() -> list[str]:
        """List frame analysis directories under the configured DLL installation."""
        return [str(path) for _, path in sorted(dump_dirs(root).items(), reverse=True)]

    @server.tool()
    def search_hash(dump: str, query: str, limit: int = 30) -> list[dict]:
        """Find an exact hash in filenames and text logs of a named frame analysis dump."""
        folder = dump_dirs(root).get(Path(dump).name)
        if folder is None:
            raise ValueError("Unknown dump. See list_dumps.")
        return hashes(folder, query, max(1, min(limit, 200)))

    @server.tool()
    def get_runtime_state() -> dict:
        """Read the latest hunting selections and profiling snapshot from an adapter build."""
        content = read_log()
        return {"selected_hashes": selection(content), "performance": performance(content),
                "last_marked": marked_hash(content), "last_frozen_fps": frozen_fps(content)}

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll-root", type=Path, required=True)
    parser.add_argument("--window", type=lambda value: int(value, 0))
    args = parser.parse_args()
    create_server(args.dll_root.resolve(strict=True), args.window).run()
