import contextlib
import json
import shlex
import shutil
import time
from argparse import ArgumentParser
from collections import ChainMap
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, NotRequired, TypedDict, cast

from caelestia.command import BaseCommand, register
from caelestia.utils import hypr
from caelestia.utils.close_guard import close_guard_active, close_guard_set
from caelestia.utils.paths import user_config_path


class SpecialWorkspace(TypedDict):
    name: str


class Monitor(TypedDict):
    focused: bool
    specialWorkspace: SpecialWorkspace


class Workspace(TypedDict):
    name: str


class Client(TypedDict):
    address: str
    workspace: Workspace
    title: NotRequired[str]
    class_: NotRequired[str]


class ConfigEntry(TypedDict, total=False):
    enable: bool
    match: list[Mapping[str, Any]]
    command: list[str]
    move: bool


def lookup(superset: Mapping[str, Any], key: str):
    if key in superset:
        return superset[key]
    aliases = {
        "class": ["initialClass"],
        "initialClass": ["class"],
        "title": ["initialTitle"],
        "initialTitle": ["title"],
        "app_id": ["class"],
    }
    for alt in aliases.get(key, []):
        if alt in superset:
            return superset[alt]
    raise KeyError(key)


def is_subset(subset: Mapping[str, Any], superset: Mapping[str, Any]) -> bool:
    for key, value in subset.items():
        try:
            superval = lookup(superset, key)
        except KeyError:
            return False

        if isinstance(value, Mapping):
            if not isinstance(superval, Mapping) or not is_subset(value, superval):
                return False

        elif isinstance(value, str):
            if not isinstance(superval, str) or value.lower() not in superval.lower():
                return False

        elif isinstance(value, list):
            if not isinstance(superval, list) or not set(value) <= set(superval):
                return False

        elif isinstance(value, set):
            if not isinstance(superval, set) or not value <= superval:
                return False

        elif value != superval:
            return False

    return True


class DeepChainMap(ChainMap):
    def __getitem__(self, key):
        values = (mapping[key] for mapping in self.maps if key in mapping)
        try:
            first = next(values)
        except StopIteration:
            return self.__missing__(key)
        if isinstance(first, dict):
            return self.__class__(first, *values)
        return first

    def __repr__(self):
        return repr(dict(self))


def specialws() -> None:
    monitors = cast(list[Monitor], hypr.message("monitors"))
    special = next(m for m in monitors if m["focused"])["specialWorkspace"]["name"]
    hypr.dispatch("togglespecialworkspace", special[8:] or "special")


def _special(name: str) -> str:
    return name if name.startswith("special:") else f"special:{name}"


def _is_special_visible_any(name: str) -> bool:
    want = _special(name)
    for m in cast(list[Monitor], hypr.message("monitors")):
        sp = m.get("specialWorkspace", {})
        if (sp.get("name") or "") == want:
            return True
    return False


def _configure(sub: ArgumentParser) -> None:
    sub.description = "Toggle Caelestia + Hyprland special workspaces"
    sub.add_argument(
        "workspace",
        help="Thing to toggle (e.g., communication, notes, music, sysmon, todo, etc.)",
    )
    sub.add_argument(
        "--notify",
        action="store_true",
        help="Show a desktop notification on toggle",
    )


@register("toggle", help="Toggle Caelestia + Hyprland special workspaces", configure_parser=_configure)
class Command(BaseCommand):
    cfg: dict[str, dict[str, ConfigEntry]] | DeepChainMap

    def __init__(self, args) -> None:
        super().__init__(args)
        self.cfg = {
            "communication": {
                "discord": {
                    "enable": True,
                    "match": [{"class": "discord"}],
                    "command": ["discord"],
                    "move": True,
                },
            },
        }
        with contextlib.suppress(FileNotFoundError, json.JSONDecodeError, KeyError):
            self.cfg = DeepChainMap(json.loads(user_config_path.read_text())["toggles"], self.cfg)

    def run(self) -> None:
        if self.args.workspace == "specialws":
            specialws()
            return

        target_name = self.args.workspace
        special_ws = _special(target_name)
        was_visible = _is_special_visible_any(target_name)
        did_work = False
        opening = not was_visible

        if target_name in self.cfg:
            for entry in cast(dict[str, ConfigEntry], self.cfg[target_name]).values():
                if entry.get("enable"):

                    def selector(c: Client) -> bool:
                        return any(is_subset(c, m) for m in list(entry.get("match", [])))

                    cmd = entry.get("command")
                    if opening and not close_guard_active(target_name):
                        if cmd and self.spawn_client(selector, cmd):
                            did_work = True
                        if entry.get("move") and self.move_client(selector, target_name):
                            did_work = True

        if opening or not did_work:
            hypr.dispatch("togglespecialworkspace", target_name)
            time.sleep(0.10)
            if not opening:
                close_guard_set(target_name)

        if did_work and opening:
            for client in self.get_clients():
                if client["workspace"]["name"] == special_ws:
                    hypr.dispatch("focuswindow", f"address:{client['address']}")
                    break

    def get_clients(self) -> list[Client]:
        return cast(list[Client], hypr.message("clients"))

    def move_client(self, selector: Callable[[Client], bool], workspace: str) -> bool:
        moved = False
        for client in self.get_clients():
            if selector(client) and client["workspace"]["name"] != _special(workspace):
                hypr.dispatch("movetoworkspacesilent", f"{_special(workspace)},address:{client['address']}")
                moved = True
        return moved

    def spawn_client(self, selector: Callable, spawn: list[str]) -> bool:
        if close_guard_active(self.args.workspace):
            return False
        if any(selector(c) for c in self.get_clients()):
            return False

        exe = spawn[0]
        have_bin = exe.endswith(".desktop") or shutil.which(exe)
        if not have_bin:
            return False

        if shutil.which("systemd-run"):
            unit = f"cae-{Path(exe).stem}-{int(time.time())}"
            argv = [
                "systemd-run",
                "--user",
                "--unit",
                unit,
                "--quiet",
                "--collect",
                "--property=KillMode=process",
                "--same-dir",
                "--",
                *spawn,
            ]
        else:
            argv = ["setsid", "-f", "--", *spawn]

        hypr_cmd = f"[workspace special:{self.args.workspace} silent] {shlex.join(argv)}"
        hypr.dispatch("exec", hypr_cmd + " </dev/null >/dev/null 2>&1")
        return True
