import subprocess
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register
from caelestia.utils.notify import notify
from caelestia.utils.paths import screenshots_cache_dir, screenshots_dir


def _capture_bytes(mode: str, freeze: bool) -> bytes:
    cmd = ["hyprshot", "-m", mode, "--raw"]
    if freeze and mode == "region":
        cmd.insert(3, "-z")
    return runner.check_bytes(cmd)


def _write_cache(sc_data: bytes) -> Path:
    screenshots_cache_dir.mkdir(parents=True, exist_ok=True)
    dest = (screenshots_cache_dir / datetime.now().strftime("%Y%m%d%H%M%S")).with_suffix(".png")
    dest.write_bytes(sc_data)
    return dest


def _handle_copy(sc_data: bytes, no_copy: bool) -> None:
    if not no_copy:
        runner.run(["wl-copy"], input=sc_data, check=True)


def _process_result(cache_path: Path) -> None:
    action = notify(
        "-i",
        "image-x-generic-symbolic",
        "-h",
        f"STRING:image-path:{cache_path}",
        "--action=open=Open",
        "--action=save=Save",
        "Screenshot taken",
        f"Screenshot stored in {cache_path} and copied to clipboard",
    )
    if action == "open":
        subprocess.Popen(["swappy", "-f", cache_path], start_new_session=True)
    elif action == "save":
        final = screenshots_dir / cache_path.name
        final.parent.mkdir(parents=True, exist_ok=True)
        cache_path.rename(final)
        notify("Screenshot saved", f"Saved to {final}")


def _configure(sub: ArgumentParser) -> None:
    mode = sub.add_mutually_exclusive_group()
    mode.add_argument("--fullscreen", action="store_true", help="Capture entire screen")
    mode.add_argument("--region", action="store_true", help="Capture a region")
    sub.add_argument("--edit", action="store_true", help="Open in swappy for annotation")
    sub.add_argument("--no-copy", action="store_true", help="Do not copy to clipboard")
    sub.add_argument("--freeze", action="store_true", help="Freeze frame during region selection")


@register("screenshot", help="Capture screenshots", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        if self.args.region:
            self.region()
        else:
            self.fullscreen()

    def fullscreen(self) -> None:
        sc_data = _capture_bytes("output", False)
        _handle_copy(sc_data, self.args.no_copy)
        cache_path = _write_cache(sc_data)
        _process_result(cache_path)

    def region(self) -> None:
        sc_data = _capture_bytes("region", self.args.freeze)
        _handle_copy(sc_data, self.args.no_copy)
        if self.args.edit:
            runner.run(["swappy", "-f", "-"], input=sc_data, check=True)
        runner.run(["qs", "-c", "caelestia", "ipc", "call", "picker", "openFreeze" if self.args.freeze else "open"])
