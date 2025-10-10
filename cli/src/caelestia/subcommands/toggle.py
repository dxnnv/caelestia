import contextlib
import json
import shlex
import shutil
from argparse import ArgumentParser
from collections import ChainMap
from collections.abc import Callable, Mapping
from typing import Any, NotRequired, TypedDict, cast

from caelestia.command import BaseCommand, register
from caelestia.utils import hypr
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


def is_subset(subset: Mapping[str, Any], superset: Mapping[str, Any]) -> bool:
    for key, value in subset.items():
        if key not in superset:
            return False

        if isinstance(value, dict):
            if not is_subset(superset[key], value):
                return False

        elif isinstance(value, str):
            if value not in superset[key]:
                return False

        elif isinstance(value, list):
            if not set(value) <= set(superset[key]):
                return False
        elif isinstance(value, set):
            if not value <= superset[key]:
                return False

        elif value != superset[key]:
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


def _configure(sub: ArgumentParser) -> None:
    sub.description = "Toggle Caelestia/Hyprland features (e.g., special workspaces)."
    sub.add_argument(
        "target",
        help="Thing to toggle (e.g., communication, notes, music, sysmon, todo, etc.)",
    )
    sub.add_argument(
        "--notify",
        action="store_true",
        help="Show a desktop notification on toggle",
    )


@register("toggle", help="Toggle features (e.g., special workspaces)", configure_parser=_configure)
class Command(BaseCommand):
    cfg: dict[str, dict[str, dict[str, Any]]] | DeepChainMap
    clients: str | dict[str, Any] | None = None

    def __init__(self, _) -> None:
        self.cfg = {
            "communication": {
                "discord": {
                    "enable": True,
                    "match": [{"class": "discord"}],
                    "command": ["discord"],
                    "move": True,
                },
                "whatsapp": {
                    "enable": True,
                    "match": [{"class": "whatsapp"}],
                    "move": True,
                },
            },
            "music": {
                "spotify": {
                    "enable": True,
                    "match": [{"class": "Spotify"}, {"initialTitle": "Spotify"}, {"initialTitle": "Spotify Free"}],
                    "command": ["spicetify", "watch", "-s"],
                    "move": True,
                },
                "feishin": {
                    "enable": True,
                    "match": [{"class": "feishin"}],
                    "move": True,
                },
            },
            "sysmon": {
                "btop": {
                    "enable": True,
                    "match": [{"class": "btop", "title": "btop", "workspace": {"name": "special:sysmon"}}],
                    "command": ["foot", "-a", "btop", "-T", "btop", "fish", "-C", "exec btop"],
                },
            },
            "todo": {
                "todoist": {
                    "enable": True,
                    "match": [{"class": "Todoist"}],
                    "command": ["todoist"],
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

        spawned = False
        if self.args.workspace in self.cfg:
            for client in self.cfg[self.args.workspace].values():
                if "enable" in client and client["enable"] and self.handle_client_config(client):
                    spawned = True

        if not spawned:
            hypr.dispatch("togglespecialworkspace", self.args.workspace)

    def get_clients(self) -> list[Client]:
        return cast(list[Client], hypr.message("clients"))

    def move_client(self, selector: Callable[[Client], bool], workspace: str) -> None:
        for client in self.get_clients():
            if selector(client) and client["workspace"]["name"] != f"special:{workspace}":
                hypr.dispatch(
                    "movetoworkspacesilent",
                    f"special:{workspace},address:{client['address']}",
                )

    def spawn_client(self, selector: Callable, spawn: list[str]) -> bool:
        if (spawn[0].endswith(".desktop") or shutil.which(spawn[0])) and not any(
            selector(client) for client in self.get_clients()
        ):
            hypr.dispatch("exec", f"[workspace special:{self.args.workspace}] app2unit -- {shlex.join(spawn)}")
            return True
        return False

    def handle_client_config(self, client: dict[str, Any]) -> bool:
        def selector(c: Client) -> bool:
            # Each match is or, inside matches is and
            return any(is_subset(c, match) for match in client["match"])

        spawned = False
        if client.get("command"):
            spawned = self.spawn_client(selector, client["command"])
        if client.get("move"):
            self.move_client(selector, self.args.workspace)

        return spawned
