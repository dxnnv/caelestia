import json
from argparse import ArgumentParser

from caelestia.command import BaseCommand, register
from caelestia.utils.wallpaper import get_colours_for_wall, get_wallpaper, set_random, set_wallpaper


def _configure(sub: ArgumentParser) -> None:
    sub.add_argument("path", nargs="?", help="Wallpaper path (defaults to current)")
    sub.add_argument("--analyze", action="store_true", help="Print derived colors/mode")
    sub.add_argument("--apply", action="store_true", help="Apply extracted palette to templates")
    sub.add_argument("--mode", choices=["auto", "light", "dark"], default="auto", help="Override inferred mode")


@register("wallpaper", help="Extract palette from wallpaper and apply", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        if self.args.print:
            print(json.dumps(get_colours_for_wall(self.args.print, self.args.no_smart)))
        elif self.args.file:
            set_wallpaper(self.args.file, self.args.no_smart)
        elif self.args.random:
            set_random(self.args)
        else:
            print(get_wallpaper() or "No wallpaper set")
