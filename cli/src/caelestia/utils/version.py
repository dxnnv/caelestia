import re
import subprocess
from pathlib import Path
from typing import Optional

import caelestia.utils.runner as runner
from caelestia.utils.paths import config_dir


def print_version() -> None:
    check_packages()

    print()
    check_meta()

    print()
    check_shell()

    print()
    check_quickshell()

    print()
    check_local()


def check_git(dir: Path, branch: str, text: bool | None) -> str | bytes:
    args = ["git", "-C", str(dir), "rev-list", "--format=%B", "--abbrev-commit", "--max-count=1", branch]
    return (
        runner.check(args, stderr=subprocess.DEVNULL) if text else runner.check_bytes(args, stderr=subprocess.DEVNULL)
    )


def parse_version_output(raw: str) -> dict[str, str]:
    parts = {}
    segments = [seg.strip() for seg in raw.split(",") if seg.strip()]

    if segments:
        parts["Version"] = segments[0]

    for seg in segments:
        if "revision" in seg:
            parts["Commit"] = seg.split("revision", 1)[1].strip()
        elif "distributed by:" in seg:
            distributor = seg.split("distributed by:", 1)[1].strip()
            if "(package:" in distributor:
                distributor = distributor.split("(package:")[0].strip()
            parts["Distributor"] = distributor

    return parts


def print_section(title: str, data: dict[str, str]):
    print(f"  ┌ {title}:")
    fields = ["Version", "Commit", "Distributor"]
    for key in fields[:-1]:
        if key in data:
            print(f"  ├─ {key}: {data[key]}")
    key = fields[-1]
    if key in data:
        print(f"  └─ {key}: {data[key]}")


def check_packages() -> None:
    if runner.installed("pacman"):
        print("  ┌ Packages:")
        pkgs = ["caelestia-shell", "caelestia-cli", "caelestia-meta"]
        versions = runner.run_proc(
            ["pacman", "-Q", *pkgs], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        ).stdout

        for pkg in pkgs:
            if pkg not in versions:
                print(f"  ├─ {pkg}: Not Found")
        print("\n".join(f"  ├─ {pkg}" for pkg in versions.splitlines()))
    else:
        print("  ├─ Packages: not on Arch")


def check_meta():
    try:
        print_git_lines(config_dir.resolve().parent, "HEAD")
    except subprocess.CalledProcessError:
        print("  ├─ Caelestia: Not Found")


def check_shell():
    try:
        raw = runner.check(["/usr/lib/caelestia/version", "-s"]).strip()
        data = parse_version_output(raw)
        print_section("Shell", data)
    except FileNotFoundError:
        print("  ├─ Shell: Version helper unavailable\n")


def check_quickshell():
    if runner.installed("qs"):
        raw = runner.check(["qs", "--version"]).strip()
        data = parse_version_output(raw)
        print_section("Quickshell", data)
    else:
        print("  ├─ Quickshell: Not Found (Missing from PATH?)\n")


def check_local():
    local_shell_dir = config_dir.parent / "caelestia"
    if local_shell_dir.exists():
        print("  Local Shell:")

        try:
            print_git_lines(local_shell_dir, "origin/master", "Upstream")
        except subprocess.CalledProcessError as e:
            print("  ─ Unable to fetch latest remote commit.")
            print(e)
            return
        print()
        print_git_lines(local_shell_dir, "HEAD")


def print_git_lines(dir: Path, branch: str, title: str | None = None):
    input = check_git(dir, branch, True)
    lines = [ln for ln in input.splitlines()[1:] if ln.strip()]
    print(f"  ┌ {title or branch} ({input.split()[1]}): ")
    for line in lines[:-1]:
        print(f"  ├─ {line}")
    print(f"  └─ {lines[-1]}")
