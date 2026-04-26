import contextlib
import json
import os
import random
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import Any

from materialyoucolor.hct import Hct
from materialyoucolor.utils.color_utils import argb_from_rgb
from PIL import Image

from caelestia.utils.hypr import message
from caelestia.utils.material import get_colours_for_image
from caelestia.utils.paths import (
    compute_hash,
    user_config_path,
    wallpaper_link_path,
    wallpaper_thumbnail_path,
    wallpapers_cache_dir,
)
from caelestia.utils.scheme import Scheme, get_scheme
from caelestia.utils.theme import apply_colours


def is_valid_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".gif"]


def check_wall(wall: Path, filter_size: tuple[int, int], threshold: float) -> bool:
    with Image.open(wall) as img:
        width, height = img.size
        return width >= filter_size[0] * threshold and height >= filter_size[1] * threshold


# --------------- symlink helpers ---------------


def _read_current_link() -> Path | None:
    p = Path(wallpaper_link_path)
    if p.exists() or p.is_symlink():
        with contextlib.suppress(OSError):
            target = p.resolve(strict=False)
            if target.is_file():
                return target
    return None


def _atomic_relink(dst_link: Path, target: Path) -> None:
    dst_link.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst_link.with_suffix(dst_link.suffix + ".tmp")
    try:
        if tmp.exists() or tmp.is_symlink():
            tmp.unlink()
        os.symlink(str(target), str(tmp))
        os.replace(tmp, dst_link)
    finally:
        if tmp.exists():
            with contextlib.suppress(OSError):
                tmp.unlink()


# -----------------------------------------------------------------------------


def get_wallpaper() -> str | None:
    current = _read_current_link()
    return str(current) if current else None


def get_wallpapers(args: Namespace) -> list[Path]:
    directory = Path(args.random)
    if not directory.is_dir():
        return []

    walls = [f for f in directory.rglob("*") if is_valid_image(f)]

    if args.no_filter:
        return walls

    monitors: dict[Any, Any] = message("monitors")
    filter_size = min(m["width"] for m in monitors), min(m["height"] for m in monitors)
    return [f for f in walls if check_wall(f, filter_size, args.threshold)]


def get_thumb(wall: Path, cache: Path) -> Path:
    thumb = cache / "thumbnail.jpg"
    if not thumb.exists():
        with Image.open(wall) as img:
            img = img.convert("RGB")
            img.thumbnail((128, 128), Image.Resampling.NEAREST)
            thumb.parent.mkdir(parents=True, exist_ok=True)
            img.save(thumb, "JPEG")
    return thumb


def get_smart_opts(wall: Path, cache: Path) -> dict[Any, Any]:
    opts_cache = cache / "smart.json"
    with contextlib.suppress(IOError, json.JSONDecodeError):
        return json.loads(opts_cache.read_text())

    from caelestia.utils.colourfulness import get_variant

    with Image.open(get_thumb(wall, cache)) as img:
        opts: dict[str, Any] = {"variant": get_variant(img)}
        img.thumbnail((1, 1), Image.Resampling.LANCZOS)
        hct = Hct.from_int(argb_from_rgb(*img.getpixel((0, 0))))
        opts["mode"] = "light" if hct.tone > 60 else "dark"

    opts_cache.parent.mkdir(parents=True, exist_ok=True)
    with opts_cache.open("w") as f:
        json.dump(opts, f)
    return opts


def get_colours_for_wall(wall: Path | str, no_smart: bool) -> dict[str, str | dict[str, str]] | None:
    wall = Path(wall)
    scheme = get_scheme()
    cache = wallpapers_cache_dir / compute_hash(wall)

    if wall.suffix.lower() == ".gif":
        wall = convert_gif(wall)

    name = "dynamic"
    if not no_smart:
        smart_opts = get_smart_opts(wall, cache)
        scheme = Scheme(
            {
                "name": name,
                "flavour": scheme.flavour,
                "mode": smart_opts["mode"],
                "variant": smart_opts["variant"],
                "colours": scheme.colours,
            }
        )

    return {
        "name": name,
        "flavour": scheme.flavour,
        "mode": scheme.mode,
        "variant": scheme.variant,
        "colours": get_colours_for_image(get_thumb(wall, cache), scheme),
    }


def convert_gif(wall: Path) -> Path:
    cache = wallpapers_cache_dir / compute_hash(wall)
    output_path = cache / "first_frame.png"

    if not output_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(wall) as img:
            try:
                img.seek(0)
            except EOFError:
                pass

            img = img.convert("RGB")
            img.save(output_path, "PNG")

    return output_path


def set_wallpaper(wall: Path | str, no_smart: bool) -> None:
    wall = Path(wall).expanduser().resolve()

    if not is_valid_image(wall):
        raise ValueError(f'"{wall}" is not a valid image')

    # Use gif's 1st frame for thumb only
    wall_cache = convert_gif(wall) if wall.suffix.lower() == ".gif" else wall

    _atomic_relink(Path(wallpaper_link_path), wall)

    cache = wallpapers_cache_dir / compute_hash(wall_cache)

    thumb = get_thumb(wall_cache, cache)
    wallpaper_thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

    _atomic_relink(Path(wallpaper_thumbnail_path), thumb)

    scheme = get_scheme()
    if scheme.name == "dynamic" and not no_smart:
        smart_opts = get_smart_opts(wall_cache, cache)
        scheme.mode = smart_opts["mode"]
        scheme.variant = smart_opts["variant"]

    scheme.update_colours()
    apply_colours(scheme.colours, scheme.mode)

    # Run custom post-hook if configured
    try:
        cfg = json.loads(user_config_path.read_text()).get("wallpaper", {})
        if post_hook := cfg.get("postHook"):
            subprocess.run(
                post_hook,
                shell=True,
                env={**os.environ, "WALLPAPER_PATH": str(wall)},
                stderr=subprocess.DEVNULL,
            )
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def set_random(args: Namespace) -> None:
    wallpapers = get_wallpapers(args)
    if not wallpapers:
        raise ValueError("No valid wallpapers found")

    current = _read_current_link()
    if current and current in wallpapers:
        wallpapers.remove(current)
        if not wallpapers:
            raise ValueError("Only valid wallpaper is current")

    set_wallpaper(random.choice(wallpapers), args.no_smart)
