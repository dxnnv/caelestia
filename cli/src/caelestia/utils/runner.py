import os
import shutil
import subprocess
from collections.abc import Sequence

StrPath = str | os.PathLike[str]


def check(cmd: Sequence[StrPath], **kw) -> str:
    installed(cmd[0])
    return subprocess.check_output(cmd, text=True, **kw)


def check_bytes(cmd: Sequence[StrPath], **kw) -> bytes:
    installed(cmd[0])
    return subprocess.check_output(cmd, text=False, **kw)


def run(cmd: Sequence[str], **kw) -> int:
    installed(cmd[0])
    return subprocess.run(cmd, **kw).returncode


def installed(cmd: StrPath):
    if not shutil.which(str(cmd)):
        raise RuntimeError(f"Missing dependency: {cmd}")
