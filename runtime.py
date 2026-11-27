"""Read diagnostics emitted by the running XXMI DLL."""
from pathlib import Path, PureWindowsPath
import re
from io import TextIOWrapper


KINDS = ("vertexbuffer", "indexbuffer", "vertexshader", "hullshader",
         "domainshader", "geometryshader", "pixelshader", "computeshader",
         "rendertarget")
ACTIONS = {"analyse_frame", "toggle_hunting", "next_marking_mode", "done_hunting",
           "monitor_performance", "freeze_performance_monitor", "reload_config"}
ACTIONS.update(f"{step}_{kind}" for kind in KINDS for step in ("next", "previous", "mark"))
ACTIONS.update({"next_vertexbuffer_slot", "previous_vertexbuffer_slot"})


def decode(raw):
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8-sig", errors="replace")


def bindings(log):
    sections = re.split(r"(?m)^\[Hunting\]\s*$", log)
    if len(sections) < 2:
        raise ValueError("No [Hunting] registration in d3d11_log.txt. Enable info logging and reload.")
    section = re.split(r"(?m)^\[", sections[-1], maxsplit=1)[0]
    result = {}
    for action, key in re.findall(r"(?m)^  ([a-z_]+)=([^\r\n]+)", section):
        if action in ACTIONS:
            result[action] = key.strip()
    return result


def hashes(folder, query, limit):
    if not re.fullmatch(r"[a-fA-F0-9]{8}|[a-fA-F0-9]{16}", query):
        raise ValueError("Expected an 8- or 16-digit hexadecimal hash")
    token = re.compile(rf"(?<![a-f0-9]){query}(?![a-f0-9])", re.I)
    matches = []
    for path in sorted(folder.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = str(path.relative_to(folder))
        if token.search(relative):
            matches.append({"file": relative})
        elif path.suffix.lower() in {".log", ".txt", ".xml"}:
            with path.open("rb") as stream:
                encoding = "utf-16" if stream.peek(2)[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
                with TextIOWrapper(stream, encoding=encoding, errors="replace") as lines:
                    for number, line in enumerate(lines, 1):
                        if token.search(line):
                            matches.append({"file": relative, "line": number,
                                            "text": line.strip()[:500]})
                            if len(matches) >= limit:
                                return matches
        if len(matches) >= limit:
            break
    return matches


def dump_dirs(root):
    return {item.name: item for item in root.glob("FrameAnalysis-*")
            if item.is_dir() and not item.is_symlink()}


def completed_dump(log, new_dirs):
    for path in reversed(re.findall(r"(?m)^Frame analysis saved to ([^\r\n]+)", log)):
        name = PureWindowsPath(path.strip()).name
        if name in new_dirs:
            return str(new_dirs[name])
    return None


def selection(log):
    body = log.rsplit("XXMI_MCP/1 selections ", 1)
    if len(body) == 1 or "\n" not in body[1]:
        return None
    selected = {}
    for kind, value in re.findall(r"(\w+)=([a-f0-9]+)", body[1].splitlines()[0]):
        selected[kind] = None if value in {"ffffffff", "ffffffffffffffff"} else value
    return selected


def performance(log):
    marker = "XXMI_MCP/1 performance begin\n"
    end = "\nXXMI_MCP/1 performance end"
    complete = log.rsplit(end, 1)[0] if end in log else ""
    return complete.rsplit(marker, 1)[-1].strip() if marker in complete else None


def marked_hash(log):
    matches = re.findall(r"(?mi)^>>>> ([^\r\n]+) marked: [^\r\n]+ hash = ([a-f0-9]{8}|[a-f0-9]{16})\s*$", log)
    if matches:
        kind, value = matches[-1]
        return {"kind": kind, "hash": value.lower()}
    return None


def frozen_fps(log):
    matches = re.findall(r"(?m)^Performance Monitor (\d+(?:\.\d+)?)fps", log)
    return float(matches[-1]) if matches else None
