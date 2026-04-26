import json
from argparse import ArgumentParser
from urllib.request import urlopen

import caelestia.utils.runner as runner
from caelestia.command import BaseCommand, register
from caelestia.utils.paths import cli_data_dir


def _configure(sub: ArgumentParser) -> None:
    sub.description = "Browse or update emoji and Nerd Font glyph data"
    mode = sub.add_mutually_exclusive_group()
    mode.add_argument(
        "--picker",
        action="store_true",
        help="Open an emoji picker using fuzzel and copy selection to clipboard.",
    )
    mode.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch and rebuild the emoji/glyph database (requires internet).",
    )
    sub.add_argument(
        "--print-path",
        action="store_true",
        help="Print the path to emojis.txt and exit.",
    )

VS16 = "\ufe0f"  # U+FE0F
ZWJ = "\u200d"

def force_emoji_presentation(s: str) -> str:
    # If it's a ZWJ sequence or already has a variation selector, leave it alone
    if ZWJ in s or VS16 in s or "\ufe0e" in s:  # VS15
        return s

    # If it's a single ambiguous symbol, VS16 forces emoji styling in many apps
    if len(s) == 1:
        return s + VS16

    return s

def fetch_emojis() -> None:
    data = [
        "¿? question upside down reversed spanish",
        "← left arrow",
        "↑ up arrow",
        "→ right arrow",
        "↓ down arrow",
        "←↑→↓ all directions up down left right arrows",
        "⇇ leftwards paired arrows",
        "⇉ rightwards paired arrows",
        "⇈ upwards paired arrows",
        "⇊ downwards paired arrows",
        "⬱ three leftwards arrows",
        "⇶ three rightwards arrows",
        "• dot circle separator",
        "「」 japanese quote square bracket",
        "¯\\_(ツ)_/¯ shrug idk i dont know",
        "(ง🔥ﾛ🔥)ง person with fire eyes eyes on fire",
        "↵ enter key return",
        "° degrees",
        "™ tm trademark",
        "® registered trademark",
        "© copyright",
        "— em dash",
        "󰖳 windows super key",
    ]

    # Fetch emojis
    with urlopen(
        "https://raw.githubusercontent.com/milesj/emojibase/refs/heads/master/packages/data/en/compact.raw.json"
    ) as f:
        emojis = json.load(f)

    for emoji in emojis:
        line = [emoji["unicode"]]

        if "emoticon" in emoji:
            if isinstance(emoji["emoticon"], str):
                line.append(emoji["emoticon"])
            else:
                line.extend(emoji["emoticon"])

        line.append(emoji["label"])

        if "tags" in emoji:
            line.extend(emoji["tags"])

        data.append(" ".join(line))

    # Fetch nerd font glyphs
    with urlopen("https://raw.githubusercontent.com/ryanoasis/nerd-fonts/refs/heads/master/glyphnames.json") as f:
        glyphs = json.load(f)

    buckets = {}
    for name, glyph in glyphs.items():
        if name == "METADATA":
            continue

        unicode = glyph["char"]
        if unicode not in buckets:
            buckets[unicode] = []
        buckets[unicode].append(f"nf-{name}")

    for glyph, names in buckets.items():
        data.append(f"{glyph}  {' '.join(names)}")

    # Write to a file
    (cli_data_dir / "emojis.txt").write_text("\n".join(data))


@register("emoji", help="Display, pick, or fetch emoji data", configure_parser=_configure)
class Command(BaseCommand):
    def run(self) -> None:
        if self.args.picker:
            emojis = (cli_data_dir / "emojis.txt").read_text()
            chosen = runner.check(["fuzzel", "--dmenu", "--placeholder=Type to search emojis"], input=emojis)
            token = chosen.split(maxsplit=1)[0]
            token = force_emoji_presentation(token)
            runner.run(["wl-copy", "-n"], input=token)
        elif self.args.fetch:
            fetch_emojis()
        else:
            print((cli_data_dir / "emojis.txt").read_text(), end="")
