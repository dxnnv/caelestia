import os
from argparse import REMAINDER, ArgumentParser
from pathlib import Path

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register


def _configure(sub: ArgumentParser) -> None:
    sub.add_argument("--print-env", action="store_true", help="Print QML2_IMPORT_PATH and exit")
    sub.add_argument("-s", dest="show", action="store_true", help="Show available IPC targets/functions")
    sub.add_argument("-m", dest="message", nargs=REMAINDER, help="IPC call: target func [args...]")
    sub.add_argument("cmd", nargs=REMAINDER, help="Command to run with QML env")


def _env_with_qml() -> dict:
    env = os.environ.copy()
    hints = [
        os.path.expanduser("~/.local/lib/qt6/qml"),
        "/usr/lib/qt6/qml",
        "/usr/local/lib/qt6/qml",
        str(Path(__file__).resolve().parents[4] / "shell" / "build" / "qml"),
    ]
    path = env.get("QML2_IMPORT_PATH", "").split(":")
    for p in hints:
        if p and os.path.isdir(p) and not path.__contains__(p):
            path.append(p)

    env["QML2_IMPORT_PATH"] = ":".join(dict.fromkeys(path))
    return env


def shell(*args: str) -> str:
    return runner.check(
        ["qs", "-c", "caelestia", *args],
        env=_env_with_qml(),
    )


@register("shell", help="Run/show IPC calls", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        if self.args.print_env:
            print("QML2_IMPORT_PATH: " + _env_with_qml().get("QML2_IMPORT_PATH", ""), end="")
            return

        if self.args.show:
            output = shell("ipc", "show").replace("target ", "").replace("function ", "")
            print(output, end="")
            return

        if self.args.message or self.args.cmd:
            print(shell("ipc", "call", *(self.args.message or self.args.cmd)), end="")
            return

        print("Nothing to do. Try: message | -s(how)")
