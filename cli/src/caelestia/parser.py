# src/caelestia/parser.py
from __future__ import annotations

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


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="caelestia",
        description="Main control script for the Caelestia toolkit",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print the current version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, meta in REGISTRY.items():
        sub = subparsers.add_parser(name, help=meta.help)
        meta.configure_parser(sub)
        sub.set_defaults(_command_cls=meta.cls)

    return parser


def parse_args() -> tuple[ArgumentParser, Namespace]:
    parser = build_parser()
    args = parser.parse_args()
    return parser, args
