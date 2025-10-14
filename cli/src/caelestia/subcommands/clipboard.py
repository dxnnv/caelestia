from argparse import ArgumentParser

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register


def _configure(sub: ArgumentParser) -> None:
    sub.add_argument("--limit", type=int, default=20, help="Max items to show from cliphist")
    sub.add_argument("--copy", type=int, metavar="INDEX", help="Copy an item by index")
    sub.add_argument("--delete", action="store_true", help="Delete entries from clipboard")


@register("clipboard", help="Manage cliphist entries", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        clip = runner.check(["cliphist", "list"])

        if self.args.delete:
            chosen = runner.check(
                ["fuzzel", "--dmenu", "--prompt=del > ", "--placeholder=Delete from clipboard"], input=clip
            )
            runner.run(["cliphist", "delete"], input=chosen)
        else:
            chosen = runner.check(["fuzzel", "--dmenu", "--placeholder=Type to search clipboard"], input=clip)
            decoded = runner.check(["cliphist", "decode"], input=chosen)
            runner.run(["wl-copy"], input=decoded)
