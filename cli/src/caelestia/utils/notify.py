import shutil
import subprocess

from caelestia.utils.runner import check


def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def notify(*args: str) -> str:
    return check(["notify-send", "-a", "caelestia-cli", *args], text=True).strip()


def close_notification(identifier: str) -> None:
    if not identifier or not _has("gdbus"):
        return

    subprocess.run(
        [
            "gdbus",
            "call",
            "--session",
            "--dest=org.freedesktop.Notifications",
            "--object-path=/org/freedesktop/Notifications",
            "--method=org.freedesktop.Notifications.CloseNotification",
            identifier,
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
