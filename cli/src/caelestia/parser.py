# src/caelestia/parser.py
from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace

from caelestia.command import REGISTRY
from caelestia.subcommands import (  # noqa: F401
    clipboard,
    emoji,
    record,
    resizer,
    scheme,
    screenshot,
    shell,
    toggle,
    wallpaper,
)


class CleanArgumentParser(ArgumentParser):
    def format_help(self):
        parts = []

        if self.description:
            parts.append(self.description)

        if self._subparsers:
            parts.append("\nCommands:")
            subparsers_action = next(
                (a for a in self._actions if isinstance(a, type(self._subparsers._group_actions[0]))), None
            )
            if subparsers_action:
                for name, sp in subparsers_action.choices.items():
                    help_text = sp.description or sp.help or ""
                    parts.append(f"  {name:<18} {help_text}")

        parts.append("\nOptions:")
        for action in self._actions:
            if action.option_strings:
                opts = ", ".join(action.option_strings)
                help_text = action.help or ""
                parts.append(f"  {opts:<20} {help_text}")

        return "\n".join(parts) + "\n"


def build_parser() -> ArgumentParser:
    parser = CleanArgumentParser(
        prog="caelestia",
        description="Main control script for the Caelestia toolkit",
        add_help=True,
        usage=argparse.SUPPRESS,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print the current version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", required=False)

    for name, meta in REGISTRY.items():
        sub = subparsers.add_parser(name, help=meta.help, description=meta.help)
        meta.configure_parser(sub)
        sub.set_defaults(_command_cls=meta.cls)

    return parser


def parse_args() -> tuple[ArgumentParser, Namespace]:
    parser = build_parser()
    args, _ = parser.parse_known_args()
    return parser, args
