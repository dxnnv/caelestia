import json
from argparse import ArgumentParser
from typing import Any

from caelestia.command import BaseCommand, register
from caelestia.utils.wallpaper import get_colours_for_wall, get_wallpaper, set_random, set_wallpaper


def _configure(sub: ArgumentParser) -> None:
    sub.add_argument("path", nargs="?", help="Wallpaper path (defaults to current)")
    sub.add_argument("-f", "--file", metavar="PATH", help="Set wallpaper to PATH")
    sub.add_argument(
        "-p",
        "--print",
        metavar="PATH",
        nargs="?",
        const="",
        help="Print derived colors JSON (for PATH, or current if omitted)",
    )
    sub.add_argument(
        "-r", "--random", metavar="DIR", help="Pick a random wallpaper from the directory (respects filtering options)"
    )
    sub.add_argument("--no-smart", action="store_true", help="Disable smart mode/variant inference")


@register("wallpaper", help="Extract palette from wallpaper and apply", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        def arg_val(key: str) -> Any:
            return getattr(self.args, key, None)

        if hasattr(self.args, "print") and self.args.print is not None:
            path = self.args.print or get_wallpaper()
            print(json.dumps(get_colours_for_wall(path, self.args.no_smart)) if path else "No wallpaper set")
        elif arg_val("random"):
            set_random(self.args)
        elif arg_val("file") or arg_val("path"):
            set_wallpaper(self.args.file or self.args.print, self.args.no_smart)
        else:
            print(get_wallpaper() or "No wallpaper set")
