from __future__ import annotations

from caelestia.parser import parse_args
from caelestia.utils.version import print_version


def main() -> int:
    parser, args = parse_args()

    if getattr(args, "version", False):
        print_version()
        return 0

    cmd_cls = getattr(args, "_command_cls", None)
    if cmd_cls is not None:
        cmd_cls(args).run()
        return 0

    parser.print_help()
    return 2
