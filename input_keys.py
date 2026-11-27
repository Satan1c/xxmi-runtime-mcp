"""Translate XXMI keyboard bindings into the host's keyboard input."""
import ctypes
import re
import subprocess
import sys
import time

MODIFIERS = {"ctrl": "Control_L", "alt": "Alt_L", "shift": "Shift_L",
             "lctrl": "Control_L", "rctrl": "Control_R", "lalt": "Alt_L",
             "ralt": "Alt_R", "lshift": "Shift_L", "rshift": "Shift_R"}
SPECIAL = {"return": ("Return", 13), "escape": ("Escape", 27),
           "space": ("space", 32), "tab": ("Tab", 9), "prior": ("Prior", 33),
           "next": ("Next", 34), "end": ("End", 35), "home": ("Home", 36),
           "left": ("Left", 37), "up": ("Up", 38), "right": ("Right", 39),
           "down": ("Down", 40), "insert": ("Insert", 45), "delete": ("Delete", 46),
           "decimal": ("KP_Decimal", 110), "divide": ("KP_Divide", 111),
           "multiply": ("KP_Multiply", 106), "subtract": ("KP_Subtract", 109),
           "add": ("KP_Add", 107), "pageup": ("Prior", 33), "pagedown": ("Next", 34)}
MODIFIER_VKS = dict(zip(MODIFIERS.values(), [162, 164, 160, 162, 163, 164, 165, 160, 161]))


def translate(binding):
    words = binding.lower().split()
    keys = []
    forbidden = []
    for word in words:
        if word.startswith("no_"):
            forbidden.append(word[3:])
            continue
        if word in MODIFIERS:
            name = MODIFIERS[word]
            keys.append((name, MODIFIER_VKS[name]))
            continue

        key = word.removeprefix("vk_")
        if key in SPECIAL:
            keys.append(SPECIAL[key])
        elif re.fullmatch(r"f(?:[1-9]|1[0-9]|2[0-4])", key):
            keys.append((key.upper(), 111 + int(key[1:])))
        elif re.fullmatch(r"[a-z0-9]", key):
            keys.append((key, ord(key.upper())))
        elif re.fullmatch(r"numpad[0-9]", key):
            keys.append(("KP_" + key[-1], 96 + int(key[-1])))
        else:
            raise ValueError(f"Unsupported keyboard token {word!r}")
    if not keys:
        raise ValueError("Empty keyboard binding")
    for word in forbidden:
        if word == "modifiers":
            if any(name in MODIFIER_VKS for name, _ in keys):
                raise ValueError("Binding both requires and excludes modifiers")
        elif any(key in keys for key in translate(word)):
            raise ValueError(f"Binding both requires and excludes {word!r}")
    return keys


def focused_window():
    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        user32.GetForegroundWindow.restype = ctypes.c_void_p
        return user32.GetForegroundWindow()
    if sys.platform == "linux":
        return int(subprocess.check_output(["xdotool", "getactivewindow"], timeout=3))
    raise RuntimeError("Keyboard input requires Windows or Linux with X11/XWayland")


def press(binding, window, hold_ms):
    keys = translate(binding)
    if not window or focused_window() != window:
        raise RuntimeError("The configured game window must have focus")

    if sys.platform == "linux":
        chord = "+".join(name for name, _ in keys)
        subprocess.run(["xdotool", "keydown", chord], check=True, timeout=3)
        try:
            time.sleep(hold_ms / 1000)
        finally:
            subprocess.run(["xdotool", "keyup", chord], check=True, timeout=3)
    else:
        send = ctypes.windll.user32.keybd_event
        pressed = []
        try:
            for _, vk in keys:
                send(vk, 0, 0, 0)
                pressed.append(vk)
            time.sleep(hold_ms / 1000)
        finally:
            for vk in reversed(pressed):
                send(vk, 0, 2, 0)
