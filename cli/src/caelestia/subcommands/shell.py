import os
from argparse import REMAINDER, ArgumentParser
from pathlib import Path

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register


def _configure(sub: ArgumentParser) -> None:
    sub.add_argument("--print-env", action="store_true", help="Print QML2_IMPORT_PATH and exit")
    sub.add_argument("cmd", nargs=REMAINDER, help="Command to run with QML env (use `--` to separate)")


@register("shell", help="Run/show IPC calls", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        output = "Nothing to do. Try: message | -s(how)"
        if self.args.show:
            output = self.shell("ipc", "show").replace("target ", "").replace("function ", "")
        elif self.args.message:
            output = self.shell("ipc", "call", *self.args.message)
        print(output, end="")

    def shell(self, *args: str) -> str:
        return runner.check(
            ["qs", "-c", "caelestia", *args],
            text=True,
            env=self._env_with_qml(),
        )

    def _env_with_qml(self) -> dict:
        env = os.environ.copy()
        hints = [
            os.path.expanduser("~/.local/lib/qt6/qml"),
            "/usr/lib/qt6/qml",
            "/usr/local/lib/qt6/qml",
            str(Path(__file__).resolve().parents[4] / "shell" / "build" / "qml"),
        ]
        existing = env.get("QML2_IMPORT_PATH", "")
        path = [p for p in hints if p and os.path.isdir(p)]
        if existing:
            path.append(existing)
        env["QML2_IMPORT_PATH"] = ":".join(dict.fromkeys(path))
        return env
