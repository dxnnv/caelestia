import json
import re
import subprocess
from pathlib import Path

from caelestia.utils.colour import get_dynamic_colours
from caelestia.utils.logging import log_exception
from caelestia.utils.paths import (
    c_state_dir,
    config_dir,
    data_dir,
    templates_dir,
    theme_dir,
    user_config_path,
    user_templates_dir,
)


def gen_conf(colours: dict[str, str]) -> str:
    conf = ""
    for name, colour in colours.items():
        conf += f"${name} = {colour}\n"
    return conf


def gen_scss(colours: dict[str, str]) -> str:
    scss = ""
    for name, colour in colours.items():
        scss += f"${name}: #{colour};\n"
    return scss


def gen_replace(colours: dict[str, str], template: Path, _hash: bool = False) -> str:
    text = template.read_text()

    for name, colour in colours.items():
        pattern = re.compile(r"\{\{\s*\$" + re.escape(name) + r"\s*\}\}")
        repl = f"#{colour}" if _hash else colour
        text = pattern.sub(repl, text)

    return text


def gen_replace_dynamic(colours: dict[str, str], template: Path) -> str:
    def fill_colour(match: re.Match) -> str:
        data = match.group(1).strip().split(".")
        if len(data) != 2:
            return match.group()
        col, form = data
        if col not in colours_dyn or not hasattr(colours_dyn[col], form):
            return match.group()
        return getattr(colours_dyn[col], form)

    # match atomic {{ . }} pairs
    field = r"\{\{((?:(?!\{\{|\}\}).)*)\}\}"
    colours_dyn = get_dynamic_colours(colours)
    template_content = template.read_text()
    template_filled = re.sub(field, fill_colour, template_content)

    return template_filled


def c2s(c: str, *i: list[int]) -> str:
    """Hex to the ANSI sequence (e.g., ffffff, 11 -> \x1b]11;rgb:ff/ff/ff\x1b\\)"""
    return f"\x1b]{';'.join(map(str, i))};rgb:{c[0:2]}/{c[2:4]}/{c[4:6]}\x1b\\"


def gen_sequences(colours: dict[str, str]) -> str:
    """
    10: foreground
    11: background
    12: cursor
    17: selection
    4:
        0 - 7: normal colours
        8 - 15: bright colours
        16+: 256 colours
    """
    return (
        c2s(colours["onSurface"], [10])
        + c2s(colours["surface"], [11])
        + c2s(colours["secondary"], [12])
        + c2s(colours["secondary"], [17])
        + c2s(colours["term0"], [4, 0])
        + c2s(colours["term1"], [4, 1])
        + c2s(colours["term2"], [4, 2])
        + c2s(colours["term3"], [4, 3])
        + c2s(colours["term4"], [4, 4])
        + c2s(colours["term5"], [4, 5])
        + c2s(colours["term6"], [4, 6])
        + c2s(colours["term7"], [4, 7])
        + c2s(colours["term8"], [4, 8])
        + c2s(colours["term9"], [4, 9])
        + c2s(colours["term10"], [4, 10])
        + c2s(colours["term11"], [4, 11])
        + c2s(colours["term12"], [4, 12])
        + c2s(colours["term13"], [4, 13])
        + c2s(colours["term14"], [4, 14])
        + c2s(colours["term15"], [4, 15])
        + c2s(colours["primary"], [4, 16])
        + c2s(colours["secondary"], [4, 17])
        + c2s(colours["tertiary"], [4, 18])
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@log_exception
def apply_terms(sequences: str) -> None:
    state = c_state_dir / "sequences.txt"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(sequences)

    pts_path = Path("/dev/pts")
    for pt in pts_path.iterdir():
        if pt.name.isdigit():
            try:
                with pt.open("a") as f:
                    f.write(sequences)
            except PermissionError:
                pass


@log_exception
def apply_hypr(conf: str) -> None:
    write_file(config_dir / "hypr/scheme/current.conf", conf)


@log_exception
def apply_discord(scss: str) -> None:
    import tempfile

    with tempfile.TemporaryDirectory("w") as tmp_dir:
        (Path(tmp_dir) / "_colours.scss").write_text(scss)
        conf = subprocess.check_output(["sass", "-I", tmp_dir, templates_dir / "discord.scss"], text=True)

    for client in ("Equicord", "Vencord", "BetterDiscord", "equibop", "vesktop", "legcord"):
        client_dir = config_dir / client / "themes"
        if client_dir.exists() and client_dir.is_dir():
            write_file(client_dir / "caelestia.theme.css", conf)


@log_exception
def apply_spicetify(colours: dict[str, str], mode: str) -> None:
    template = gen_replace(colours, templates_dir / f"spicetify-{mode}.ini")
    write_file(config_dir / "spicetify/Themes/caelestia/color.ini", template)


@log_exception
def apply_fuzzel(colours: dict[str, str]) -> None:
    template = gen_replace(colours, templates_dir / "fuzzel.ini")
    write_file(config_dir / "fuzzel/fuzzel.ini", template)


@log_exception
def apply_btop(colours: dict[str, str]) -> None:
    template = gen_replace(colours, templates_dir / "btop.theme", _hash=True)
    write_file(config_dir / "btop/themes/caelestia.theme", template)
    subprocess.run(["killall", "-USR2", "btop"], stderr=subprocess.DEVNULL)


@log_exception
def apply_nvtop(colours: dict[str, str]) -> None:
    template = gen_replace(colours, templates_dir / "nvtop.colors", _hash=True)
    write_file(config_dir / "nvtop/nvtop.colors", template)


@log_exception
def apply_htop(colours: dict[str, str]) -> None:
    template = gen_replace(colours, templates_dir / "htop.theme", _hash=True)
    write_file(config_dir / "htop/htoprc", template)
    subprocess.run(["killall", "-USR2", "htop"], stderr=subprocess.DEVNULL)


@log_exception
def apply_gtk(colours: dict[str, str], mode: str) -> None:
    template = gen_replace(colours, templates_dir / "gtk.css", _hash=True)
    write_file(config_dir / "gtk-3.0/gtk.css", template)
    write_file(config_dir / "gtk-4.0/gtk.css", template)

    subprocess.run(["dconf", "write", "/org/gnome/desktop/interface/gtk-theme", "'adw-gtk3-dark'"])
    subprocess.run(["dconf", "write", "/org/gnome/desktop/interface/color-scheme", f"'prefer-{mode}'"])
    subprocess.run(["dconf", "write", "/org/gnome/desktop/interface/icon-theme", f"'Papirus-{mode.capitalize()}'"])


@log_exception
def apply_qt(colours: dict[str, str], mode: str) -> None:
    template = gen_replace(colours, templates_dir / f"qt{mode}.colors", _hash=True)
    write_file(config_dir / "qt5ct/colors/caelestia.colors", template)
    write_file(config_dir / "qt6ct/colors/caelestia.colors", template)

    qtct = (templates_dir / "qtct.conf").read_text()
    qtct = qtct.replace("{{ $mode }}", mode.capitalize())

    for ver in 5, 6:
        conf = qtct.replace("{{ $config }}", str(config_dir / f"qt{ver}ct"))

        if ver == 5:
            conf += """
[Fonts]
fixed="Monospace,12,-1,5,50,0,0,0,0,0"
general="Sans Serif,12,-1,5,50,0,0,0,0,0"
"""
        else:
            conf += """
[Fonts]
fixed="Monospace,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
general="Sans Serif,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
"""
        write_file(config_dir / f"qt{ver}ct/qt{ver}ct.conf", conf)


@log_exception
def apply_warp(colours: dict[str, str], mode: str) -> None:
    warp_mode = "darker" if mode == "dark" else "lighter"

    template = gen_replace(colours, templates_dir / "warp.yaml", _hash=True)
    template = template.replace("{{ $warp_mode }}", warp_mode)
    write_file(data_dir / "warp-terminal/themes/caelestia.yaml", template)


@log_exception
def apply_cava(colours: dict[str, str]) -> None:
    template = gen_replace(colours, templates_dir / "cava.conf", _hash=True)
    write_file(config_dir / "cava/config", template)
    subprocess.run(["killall", "-USR2", "cava"], stderr=subprocess.DEVNULL)


@log_exception
def apply_kitty(colours: dict[str, str]) -> None:
    theme_text = gen_replace(colours, templates_dir / "kitty.conf", _hash=True)
    theme_path = config_dir / "kitty/themes/caelestia.conf"
    write_file(theme_path, theme_text)

    try:
        subprocess.run(
            ["kitty", "@", "set-colors", "--all", "--configured", str(theme_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            ["kitty", "@", "set-colors", "--all", "selection_background=" + "#" + colours["secondary"]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        pass


@log_exception
def apply_user_templates(colours: dict[str, str]) -> None:
    if not user_templates_dir.is_dir():
        return

    for file in user_templates_dir.iterdir():
        if file.is_file():
            content = gen_replace_dynamic(colours, file)
            write_file(theme_dir / file.name, content)


@log_exception
def run_fastfetch(colours: dict[str, str]) -> None:
    def hexc(key: str) -> str:
        return f"#{colours[key]}"

    args = [
        "fastfetch",
        "--color-keys",
        hexc("secondary"),
        "--color-title",
        hexc("primary"),
        "--percent-color-green",
        hexc("primary"),
        "--percent-color-yellow",
        hexc("tertiary"),
        "--percent-color-red",
        hexc("term9"),
        "--logo-color-1",
        hexc("primary"),
        "--logo-color-2",
        hexc("secondary"),
        "--logo-color-3",
        hexc("tertiary"),
        "--logo-color-4",
        hexc("onSurface"),
    ]
    try:
        subprocess.run(args, check=False)
    except FileNotFoundError:
        pass


def apply_colours(colours: dict[str, str], mode: str) -> None:
    try:
        cfg = json.loads(user_config_path.read_text())["theme"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        cfg = {}

    def check(key: str) -> bool:
        return cfg[key] if key in cfg else True

    if check("enableTerm"):
        apply_terms(gen_sequences(colours))
    if check("enableHypr"):
        apply_hypr(gen_conf(colours))
    if check("enableDiscord"):
        apply_discord(gen_scss(colours))
    if check("enableSpicetify"):
        apply_spicetify(colours, mode)
    if check("enableFuzzel"):
        apply_fuzzel(colours)
    if check("enableBtop"):
        apply_btop(colours)
    if check("enableNvtop"):
        apply_nvtop(colours)
    if check("enableHtop"):
        apply_htop(colours)
    if check("enableGtk"):
        apply_gtk(colours, mode)
    if check("enableQt"):
        apply_qt(colours, mode)
    if check("enableWarp"):
        apply_warp(colours, mode)
    if check("enableCava"):
        apply_cava(colours)
    if check("enableKitty"):
        apply_kitty(colours)
    run_fastfetch(colours)
    apply_user_templates(colours)
