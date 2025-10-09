import os
import subprocess
from argparse import Namespace
from pathlib import Path


class Command:
    args: Namespace

    def __init__(self, args: Namespace) -> None:
        self.args = args

    def run(self) -> None:
        output = "Nothing to do. Try: message | -s(how)"
        if self.args.show:
            output = self.shell("ipc", "show").replace("target ", "").replace("function ", "")
        elif self.args.message:
            output = self.shell("ipc", "call", *self.args.message)
        print(output, end="")

    def shell(self, *args: str) -> str:
        return subprocess.check_output(
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
