import json
import os
import socket
from typing import Any


def socket_paths() -> tuple[str, str]:
    xdg = os.getenv("XDG_RUNTIME_DIR")
    sig = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
    if not xdg or not sig:
        raise RuntimeError("Hyprland not detected (missing XDG_RUNTIME_DIR or HYPRLAND_INSTANCE_SIGNATURE).")
    base = f"{xdg}/hypr/{sig}"
    return f"{base}/.socket.sock", f"{base}/.socket2.sock"


def message(msg: str, is_json: bool = True) -> str | dict[str, Any]:
    sock_path, _ = socket_paths()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sock_path)

        if is_json:
            msg = f"j/{msg}"
        sock.send(msg.encode())

        resp = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            resp.append(chunk)
        data = b"".join(resp).decode()
        return json.loads(data) if is_json else data


def dispatch(dispatcher: str, *args: str) -> bool:
    return message(f"dispatch {dispatcher} {' '.join(map(str, args))}".rstrip(), is_json=False) == "ok"


def batch(*msgs: str, json: bool = False) -> str | dict[str, Any]:
    msgs = tuple((f"j/{m.strip()}" if json else m.strip()) for m in msgs)
    return message(f"[[BATCH]]{';'.join(msgs)}", is_json=False)
