import contextlib
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _env_path(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default))).expanduser()


config_dir = _env_path("XDG_CONFIG_HOME", Path.home() / ".config")
data_dir = _env_path("XDG_DATA_HOME", Path.home() / ".local" / "share")
state_dir = _env_path("XDG_STATE_HOME", Path.home() / ".local" / "state")
cache_dir = _env_path("XDG_CACHE_HOME", Path.home() / ".cache")

pictures_dir = _env_path("XDG_PICTURES_DIR", Path.home() / "Pictures")
videos_dir = _env_path("XDG_VIDEOS_DIR", Path.home() / "Videos")

c_config_dir = config_dir / "caelestia"
c_data_dir = data_dir / "caelestia"
c_state_dir = state_dir / "caelestia"
c_cache_dir = cache_dir / "caelestia"

user_config_path = c_config_dir / "cli.json"
cli_data_dir = Path(__file__).parent.parent / "data"
templates_dir = cli_data_dir / "templates"
user_templates_dir = c_config_dir / "templates"
theme_dir = c_state_dir / "theme"

scheme_path = c_state_dir / "scheme.json"
scheme_data_dir = cli_data_dir / "schemes"
scheme_cache_dir = c_cache_dir / "schemes"

wallpapers_dir = _env_path("CAELESTIA_WALLPAPERS_DIR", pictures_dir / "Wallpapers")
wallpaper_path_path = c_state_dir / "wallpaper" / "path.txt"
wallpaper_link_path = c_state_dir / "wallpaper" / "current"
wallpaper_thumbnail_path = c_state_dir / "wallpaper" / "thumbnail.jpg"
wallpapers_cache_dir = c_cache_dir / "wallpapers"

screenshots_dir = _env_path("CAELESTIA_SCREENSHOTS_DIR", pictures_dir / "Screenshots")
screenshots_cache_dir = c_cache_dir / "screenshots"

recordings_dir = _env_path("CAELESTIA_RECORDINGS_DIR", videos_dir / "Recordings")
recording_path = c_state_dir / "record" / "recording.mp4"
recording_notif_path = c_state_dir / "record" / "notifid.txt"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def compute_hash(path: Path | str) -> str:
    sha = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def atomic_dump(path: Path, content: dict[str, Any]) -> None:
    path = Path(path)
    ensure_parent(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()
