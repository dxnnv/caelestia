import contextlib
import json
import os
import time

_GUARD_DIR = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "caelestia", "special-guard")


def _guard_path(name: str) -> str:
    return os.path.join(_GUARD_DIR, f"{name}.json")


def close_guard_set(name: str, ms: int = 800) -> None:
    os.makedirs(_GUARD_DIR, exist_ok=True)
    path = _guard_path(name)
    tmp = f"{path}.tmp"
    until = time.time() + ms / 1000.0
    with open(tmp, "w") as f:
        json.dump({"until": until}, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)  # atomic


def close_guard_active(name: str) -> bool:
    path = _guard_path(name)
    try:
        with open(path) as f:
            data = json.load(f)
        until = float(data.get("until", 0))
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError, OSError):
        return False

    if time.time() < until:
        return True

    with contextlib.suppress(OSError):
        os.remove(path)
    return False
