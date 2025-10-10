from argparse import ArgumentParser

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register


def _configure(sub: ArgumentParser) -> None:
    sub.add_argument("--limit", type=int, default=20, help="Max items to show from cliphist")
    sub.add_argument("--copy", type=int, metavar="INDEX", help="Copy an item by index")


@register("clipboard", help="Manage cliphist entries", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        clip = runner.check(["cliphist", "list"])

        if self.args.delete:
            args = ["--prompt=del > ", "--placeholder=Delete from clipboard"]
        else:
            args = ["--placeholder=Type to search clipboard"]

        chosen = runner.check(["fuzzel", "--dmenu", *args], input=clip)

        if self.args.delete:
            runner.run(["cliphist", "delete"], input=chosen)
        else:
            decoded = runner.check(["cliphist", "decode"], input=chosen)
            runner.run(["wl-copy"], input=decoded)
