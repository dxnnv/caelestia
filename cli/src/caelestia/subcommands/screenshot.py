import subprocess
from argparse import ArgumentParser
from datetime import datetime

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register
from caelestia.utils.notify import notify
from caelestia.utils.paths import screenshots_cache_dir, screenshots_dir


def fullscreen() -> None:
    sc_data = runner.check_bytes(["grim", "-"])
    subprocess.run(["wl-copy"], input=sc_data, check=True)

    dest = screenshots_cache_dir / datetime.now().strftime("%Y%m%d%H%M%S")
    screenshots_cache_dir.mkdir(exist_ok=True, parents=True)
    dest.write_bytes(sc_data)

    action = notify(
        "-i",
        "image-x-generic-symbolic",
        "-h",
        f"STRING:image-path:{dest}",
        "--action=open=Open",
        "--action=save=Save",
        "Screenshot taken",
        f"Screenshot stored in {dest} and copied to clipboard",
    )

    if action == "open":
        subprocess.Popen(["swappy", "-f", dest], start_new_session=True)
    elif action == "save":
        new_dest = (screenshots_dir / dest.name).with_suffix(".png")
        new_dest.parent.mkdir(exist_ok=True, parents=True)
        dest.rename(new_dest)
        notify("Screenshot saved", f"Saved to {new_dest}")


def _configure(sub: ArgumentParser) -> None:
    mode = sub.add_mutually_exclusive_group()
    mode.add_argument("--fullscreen", action="store_true", help="Capture entire screen")
    mode.add_argument("--region", metavar="WxH+X+Y", help="Capture a region")
    sub.add_argument("--edit", action="store_true", help="Open in swappy for annotation")
    sub.add_argument("--no-copy", action="store_true", help="Do not copy to clipboard")


@register("screenshot", help="Capture screenshots", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        if self.args.region:
            self.region()
        else:
            fullscreen()

    def region(self) -> None:
        if self.args.region == "slurp":
            subprocess.run(
                ["qs", "-c", "caelestia", "ipc", "call", "picker", "openFreeze" if self.args.freeze else "open"]
            )
        else:
            sc_data: bytes = runner.check_bytes(["grim", "-l", "0", "-g", self.args.region.strip(), "-"])
            swappy = subprocess.Popen(["swappy", "-f", "-"], stdin=subprocess.PIPE, start_new_session=True)
            if swappy.stdin is not None:
                swappy.stdin.write(sc_data)
                swappy.stdin.close()
