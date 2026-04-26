import contextlib
import fcntl
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import caelestia.utils.runner as runner
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
    new_template = template.read_text()
    for name, colour in colours.items():
        pattern = r"\{\{\s*\$" + re.escape(name) + r"\s*\}\}"
        new_template = re.sub(pattern, ("#" if _hash else "") + colour, new_template)
    return new_template


def gen_replace_dynamic(colours: dict[str, str], template: Path, mode: str) -> str:
    def fill_colour(match: re.Match) -> str:
        data = match.group(1).strip().split(".")
        if len(data) != 2:
            return match.group()
        col, form = data
        if col not in colours_dyn or not hasattr(colours_dyn[col], form):
            return match.group()
        return getattr(colours_dyn[col], form)

    # match atomic {{ . }} pairs
    dotField = r"\{\{((?:(?!\{\{|\}\}).)*)\}\}"

    # match {{ mode }}
    modeField = r"\{\{\s*mode\s*\}\}"

    colours_dyn = get_dynamic_colours(colours)
    template_content = template.read_text()

    template_filled = re.sub(dotField, fill_colour, template_content)
    template_filled = re.sub(modeField, mode, template_filled)

    return template_filled


def hex_to_ansi(c: str, *i: int) -> str:
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
        hex_to_ansi(colours["onSurface"], 10)
        + hex_to_ansi(colours["surface"], 11)
        + hex_to_ansi(colours["secondary"], 12)
        + hex_to_ansi(colours["secondary"], 17)
        + hex_to_ansi(colours["term0"], 4, 0)
        + hex_to_ansi(colours["term1"], 4, 1)
        + hex_to_ansi(colours["term2"], 4, 2)
        + hex_to_ansi(colours["term3"], 4, 3)
        + hex_to_ansi(colours["term4"], 4, 4)
        + hex_to_ansi(colours["term5"], 4, 5)
        + hex_to_ansi(colours["term6"], 4, 6)
        + hex_to_ansi(colours["term7"], 4, 7)
        + hex_to_ansi(colours["term8"], 4, 8)
        + hex_to_ansi(colours["term9"], 4, 9)
        + hex_to_ansi(colours["term10"], 4, 10)
        + hex_to_ansi(colours["term11"], 4, 11)
        + hex_to_ansi(colours["term12"], 4, 12)
        + hex_to_ansi(colours["term13"], 4, 13)
        + hex_to_ansi(colours["term14"], 4, 14)
        + hex_to_ansi(colours["term15"], 4, 15)
        + hex_to_ansi(colours["primary"], 4, 16)
        + hex_to_ansi(colours["secondary"], 4, 17)
        + hex_to_ansi(colours["tertiary"], 4, 18)
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w") as f:
        f.write(content)
        f.flush()
        shutil.move(f.name, path)


@log_exception
def apply_terms(sequences: str) -> None:
    state = c_state_dir / "sequences.txt"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(sequences)

    pts_path = Path("/dev/pts")
    for pt in pts_path.iterdir():
        if pt.name.isdigit():
            with contextlib.suppress(PermissionError):
                # Use non-blocking write with timeout to prevent hangs
                import os

                fd = os.open(str(pt), os.O_WRONLY | os.O_NONBLOCK | os.O_NOCTTY)
                try:
                    os.write(fd, sequences.encode())
                finally:
                    os.close(fd)


@log_exception
def apply_hypr(conf: str) -> None:
    write_file(config_dir / "hypr/scheme/current.conf", conf)


@log_exception
def apply_discord(scss: str) -> None:
    import tempfile

    with tempfile.TemporaryDirectory("w") as tmp_dir:
        (Path(tmp_dir) / "_colours.scss").write_text(scss)
        conf = runner.check(["sass", "-I", tmp_dir, templates_dir / "discord.scss"])

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


def sync_papirus_colors(hex_color: str) -> None:
    """Sync Papirus folder icon colors using hue/saturation analysis"""
    try:
        result = subprocess.run(["which", "papirus-folders"], capture_output=True, check=False)
        if result.returncode != 0:
            return
    except Exception:
        return

    papirus_paths = [
        Path("/usr/share/icons/Papirus"),
        Path("/usr/share/icons/Papirus-Dark"),
        Path.home() / ".local/share/icons/Papirus",
        Path.home() / ".icons/Papirus",
    ]

    if not any(p.exists() for p in papirus_paths):
        return

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Brightness and saturation
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    brightness = max_val
    saturation = 0 if max_val == 0 else ((max_val - min_val) * 100) // max_val

    # Low saturation = grayscale
    if saturation < 20:
        if brightness < 85:
            color = "black"
        elif brightness < 170:
            color = "grey"
        else:
            color = "white"
    # Medium-low saturation with high brightness = pale variants
    elif saturation < 60 and brightness > 180:
        use_pale = True
        color = _determine_hue_color(r, g, b, brightness, use_pale)
    else:
        color = _determine_hue_color(r, g, b, brightness, False)

    try:
        subprocess.Popen(
            ["sudo", "-n", "papirus-folders", "-C", color, "-u"],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def _determine_hue_color(r: int, g: int, b: int, brightness: int, use_pale: bool) -> str:
    if b > r and b > g:
        # Blue dominant
        r_ratio = (r * 100) // b if b > 0 else 0
        g_ratio = (g * 100) // b if b > 0 else 0
        rg_diff = abs(r - g)

        if r_ratio > 70 and g_ratio > 70:
            # Both R and G high relative to B = light blue/periwinkle
            if rg_diff < 15:
                return "blue"
            elif r > g:
                return "violet"
            else:
                return "cyan"
        elif r_ratio > 60 and r > g:
            return "violet"
        elif g_ratio > 60 and g > r:
            return "cyan"
        else:
            return "blue"
    elif r > g and r > b:
        # Red dominant
        if g > b + 30:
            # Orange/yellow-ish/brown
            rg_ratio = (g * 100) // r if r > 0 else 0
            if use_pale:
                if rg_ratio > 70 and brightness < 220:
                    return "palebrown"
                else:
                    return "paleorange"
            else:
                if rg_ratio > 70 and brightness < 180:
                    return "brown"
                else:
                    return "orange"
        elif b > g + 20:
            return "pink"
        else:
            return "pink" if use_pale else "red"
    elif g > r and g > b:
        # Green dominant
        if r > b + 30:
            return "yellow"
        else:
            return "green"
    else:
        return "grey"


@log_exception
def apply_gtk(colours: dict[str, str], mode: str) -> None:
    template = gen_replace(colours, templates_dir / "gtk.css", _hash=True)
    write_file(config_dir / "gtk-3.0/gtk.css", template)
    write_file(config_dir / "gtk-4.0/gtk.css", template)

    subprocess.run(["dconf", "write", "/org/gnome/desktop/interface/gtk-theme", "'adw-gtk3-dark'"])
    subprocess.run(["dconf", "write", "/org/gnome/desktop/interface/color-scheme", f"'prefer-{mode}'"])
    subprocess.run(["dconf", "write", "/org/gnome/desktop/interface/icon-theme", f"'Papirus-{mode.capitalize()}'"])

    sync_papirus_colors(colours["primary"])


@log_exception
def apply_qt(colours: dict[str, str], mode: str) -> None:
    replaced = gen_replace(colours, templates_dir / f"qt{mode}.colors", _hash=True)
    write_file(config_dir / "qtengine/caelestia.colors", replaced)

    config = (templates_dir / "qtengine.json").read_text()
    config = config.replace("{{ $mode }}", mode.capitalize())
    write_file(config_dir / "qtengine/config.json", config)


@log_exception
def apply_warp(colours: dict[str, str], mode: str) -> None:
    warp_mode = "darker" if mode == "dark" else "lighter"

    template = gen_replace(colours, templates_dir / "warp.yaml", _hash=True)
    template = template.replace("{{ $warp_mode }}", warp_mode)
    write_file(data_dir / "warp-terminal/themes/caelestia.yaml", template)


@log_exception
def apply_chromium(colours: dict[str, str]) -> None:
    surface_hex = colours["surface"]
    theme_color = f"#{surface_hex}"
    browsers = [
        ("chromium", Path("/etc/chromium/policies/managed")),
        ("brave", Path("/etc/brave/policies/managed")),
        ("google-chrome-stable", Path("/etc/opt/chrome/policies/managed")),
    ]

    for cmd, policy_dir in browsers:
        if shutil.which(cmd) is None:
            continue
        if not policy_dir.is_dir():
            subprocess.run(["sudo", "-n", "mkdir", "-p", str(policy_dir)], stderr=subprocess.DEVNULL)
        if not policy_dir.is_dir():
            print(f"Unable to create {policy_dir} directory")
            continue

        # Use tee instead of write_file cause we need sudo
        subprocess.run(
            ["sudo", "-n", "tee", str(policy_dir / "caelestia.json")],
            input=json.dumps({"BrowserThemeColor": theme_color, "BrowserColorScheme": "device"}),
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            [cmd, "--refresh-platform-policy", "--no-startup-window"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


@log_exception
def apply_zed(colours: dict[str, str], mode: str) -> None:
    theme_path = config_dir / "zed/themes/caelestia.json"
    # Zed's file watcher does not detect changes through symlinks,
    # so resolve to a regular file before writing
    if theme_path.is_symlink():
        theme_path.unlink()

    content = gen_replace_dynamic(colours, templates_dir / "zed.json", mode)
    write_file(theme_path, content)


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

    with contextlib.suppress(FileNotFoundError):
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


@log_exception
def apply_swaync(colours: dict[str, str]) -> None:
    with contextlib.suppress(FileNotFoundError):
        css = gen_replace(colours, templates_dir / "swaync.css", _hash=True)
        write_file(config_dir / "swaync/style.css", css)
        subprocess.run(["swaync-client", "--reload-css"], check=False)

    def define(name: str, hex: str) -> str:
        return f"@define-color {name} #{hex};\n"

    lines: list[str] = []
    for key, hexval in colours.items():
        keb = re.sub(r"(?<!^)([A-Z])", r"-\1", key).replace("_", "-").lower()
        und = keb.replace("-", "_")
        lines.append(define(keb, hexval))
        if und != keb:
            lines.append(define(und, hexval))

    alias_map = {
        "blur_background": "surface-dim",
        "groupbackground": "surface-dim",
        "buttoncolor": "primary",
        "bordercolor": "inverse-primary",
        "fontcolor": "on-surface",
        "source_color": "primary",
        "background": "surface",
        "on_background": "on-surface",
        "on_secondary": "on-secondary",
        "primary_fixed_dim": "primary-fixed-dim",
        "primary_fixed": "primary-fixed",
        "on_primary": "on-primary",
        "inverse_primary": "inverse-primary",
        "on_surface_variant": "on-surface-variant",
        "scrim": "scrim",
    }

    for alias, target in alias_map.items():
        lines.append(f"@define-color {alias} @{target};\n")

    colors_css = "".join(lines)
    write_file(config_dir / "swaync/colors.css", colors_css)

    with contextlib.suppress(FileNotFoundError):
        css = gen_replace(colours, templates_dir / "swaync.css", _hash=True)
        write_file(config_dir / "swaync/style.css", css)

    with contextlib.suppress(FileNotFoundError):
        subprocess.run(["swaync-client", "--reload-config"], check=False)
        subprocess.run(["swaync-client", "--reload-css"], check=False)


@log_exception
def apply_user_templates(colours: dict[str, str], mode: str) -> None:
    if not user_templates_dir.is_dir():
        return

    for file in user_templates_dir.iterdir():
        if file.is_file():
            content = gen_replace_dynamic(colours, file, mode)
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
    with contextlib.suppress(FileNotFoundError):
        subprocess.run(args, check=False)


def apply_colours(colours: dict[str, str], mode: str) -> None:
    # Use file-based lock to prevent concurrent theme changes
    lock_file = c_state_dir / "theme.lock"
    c_state_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(lock_file, "w") as lock_fd:
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return

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
            if check("enableZed"):
                apply_zed(colours, mode)
            if check("enableChromium"):
                apply_chromium(colours)
            if check("enableCava"):
                apply_cava(colours)
            if check("enableKitty"):
                apply_kitty(colours)
            if check("enableSwayNC"):
                apply_swaync(colours)
            run_fastfetch(colours)
            apply_user_templates(colours, mode)

    finally:
        try:
            lock_file.unlink()
        except FileNotFoundError:
            pass
