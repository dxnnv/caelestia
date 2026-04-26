import contextlib
import json
import re
import shutil
import subprocess
import time
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register
from caelestia.utils.notify import close_notification, notify
from caelestia.utils.paths import recording_notif_path, recording_path, recordings_dir, user_config_path

RECORDER = "gpu-screen-recorder"


def proc_running() -> bool:
    return subprocess.run(["pidof", RECORDER], stdout=subprocess.DEVNULL).returncode == 0


def intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]


def _configure(sub: ArgumentParser) -> None:
    act = sub.add_mutually_exclusive_group(required=True)
    act.add_argument("--start", action="store_true", help="Start recording")
    act.add_argument("--stop", action="store_true", help="Stop recording")
    act.add_argument("--pause", action="store_true", help="Pause recording")
    act.add_argument("-c", "--clipboard", action="store_true", help="copy recording path to clipboard")
    act.add_argument("--resume", action="store_true", help="Resume recording")
    sub.add_argument("--region", metavar="WxH+X+Y", help="Region to record")
    sub.add_argument("--fps", type=int, default=60, help="Frames per second")
    sub.add_argument("--output", type=str, help="Output file path")


@register("record", help="Screen recording", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        if self.args.pause:
            subprocess.run(["pkill", "-USR2", "-f", RECORDER], stdout=subprocess.DEVNULL)
        elif proc_running():
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        args = ["-w"]

        monitors = json.loads(runner.check(["hyprctl", "monitors", "-j"]))
        if self.args.region:
            if self.args.region == "slurp":
                region = runner.check(["slurp", "-f", "%wx%h+%x+%y"], text=True)
            else:
                region = self.args.region.strip()
            args += ["region", "-region", region]

            m = re.match(r"(\d+)x(\d+)\+(\d+)\+(\d+)", region)
            if not m:
                raise ValueError(f"Invalid region: {region}")

            w, h, x, y = map(int, m.groups())
            r = x, y, w, h
            max_rr = 0
            for monitor in monitors:
                if intersects((monitor["x"], monitor["y"], monitor["width"], monitor["height"]), r):
                    rr = round(monitor["refreshRate"])
                    max_rr = max(max_rr, rr)
            args += ["-f", str(max_rr)]
        else:
            focused_monitor = next(monitor for monitor in monitors if monitor["focused"])
            if focused_monitor:
                args += [focused_monitor["name"], "-f", str(round(focused_monitor["refreshRate"]))]

        if self.args.sound:
            args += ["-a", "default_output"]

        try:
            config = json.loads(user_config_path.read_text())
            if "record" in config and "extraArgs" in config["record"]:
                args += config["record"]["extraArgs"]
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        except TypeError as e:
            raise ValueError(f"Config option 'record.extraArgs' should be an array: {e}") from e

        recording_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen([RECORDER, *args, "-o", str(recording_path)], start_new_session=True)

        notif = notify("-p", "Recording started", "Recording...")
        recording_notif_path.write_text(notif)

        try:
            if proc.wait(1) != 0:
                close_notification(notif)
                notify(
                    "Recording failed",
                    "An error occurred attempting to start recorder. "
                    f"Command `{' '.join(args)}` failed with exit code {proc.returncode}",
                )
        except subprocess.TimeoutExpired:
            pass

    def stop(self) -> None:
        # Start killing the recording process
        subprocess.run(["pkill", "-f", RECORDER], stdout=subprocess.DEVNULL)

        # Wait for the recording to finish to avoid a corrupted video file
        while proc_running():
            time.sleep(0.1)

        # Move to the recordings folder
        new_path = recordings_dir / f"recording_{datetime.now().strftime('%Y%m%d_%H-%M-%S')}.mp4"
        recordings_dir.mkdir(exist_ok=True, parents=True)
        shutil.move(recording_path, new_path)

        # Close start notification
        with contextlib.suppress(IOError):
            close_notification(recording_notif_path.read_text())

        if self.args.clipboard:
            file_uri = Path(new_path).resolve().as_uri() + "\n"
            subprocess.run(["wl-copy", "--type", "text/uri-list"], input=file_uri.encode())

        action = notify(
            "--action=watch=Watch",
            "--action=open=Open",
            "--action=delete=Delete",
            "Recording stopped",
            f"Recording saved in {new_path}",
        )

        if action == "watch":
            subprocess.Popen(["app2unit", "-O", new_path], start_new_session=True)
        elif action == "open":
            p = subprocess.run(
                [
                    "dbus-send",
                    "--session",
                    "--dest=org.freedesktop.FileManager1",
                    "--type=method_call",
                    "/org/freedesktop/FileManager1",
                    "org.freedesktop.FileManager1.ShowItems",
                    f"array:string:file://{new_path}",
                    "string:",
                ]
            )
            if p.returncode != 0:
                subprocess.Popen(["app2unit", "-O", new_path.parent], start_new_session=True)
        elif action == "delete":
            new_path.unlink()
