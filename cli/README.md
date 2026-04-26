# caelestia-cli

The main control script for the Caelestia dotfiles.

<details><summary id="dependencies">External dependencies</summary>

- [`app2unit`](https://github.com/Vladimir-csp/app2unit) - launching apps
- [`cliphist`](https://github.com/sentriz/cliphist) - clipboard history
- [`dart-sass`](https://github.com/sass/dart-sass) - discord theming
- [`fuzzel`](https://codeberg.org/dnkl/fuzzel) - clipboard history/emoji picker
- `glib2` - closing notifications
- [`gpu-screen-recorder`](https://git.dec05eba.com/gpu-screen-recorder/about) - screen recording
- `hyprshot` - taking screenshots
- [`libnotfy`](https://gitlab.gnome.org/GNOME/libnotify) - sending notifications
- [`slurp`](https://github.com/emersion/slurp) - selecting an area
- [`swappy`](https://github.com/jtheoof/swappy) - screenshot editor
- [`wl-clipboard`](https://github.com/bugaevc/wl-clipboard) - copying to clipboard

- [`python-build`](https://github.com/pypa/build)
- [`python-installer`](https://github.com/pypa/installer)
- [`python-hatch`](https://github.com/pypa/hatch)
- [`python-hatch-vcs`](https://github.com/ofek/hatch-vcs)

</details>

<details><summary id="optional-dependencies">Optional dependencies</summary>

- [`papirus-folders`](https://github.com/PapirusDevelopmentTeam/papirus-folders) - automatic folder icon color syncing with theme

> [!NOTE]
> For automatic Papirus folder icon color syncing, `papirus-folders` needs to be able to run with `sudo` without a password prompt.
>
> **Recommended** - Create a sudoers file:
>
> ```fish
> # Fish shell
> echo "$USER ALL=(ALL) NOPASSWD: "(which papirus-folders) | sudo tee /etc/sudoers.d/papirus-folders
> sudo chmod 440 /etc/sudoers.d/papirus-folders
> ```
>
> ```sh
> # Bash/other shells
> echo "$USER ALL=(ALL) NOPASSWD: $(which papirus-folders)" | sudo tee /etc/sudoers.d/papirus-folders
> sudo chmod 440 /etc/sudoers.d/papirus-folders
> ```
>
> **Alternatively** - Edit the main sudoers file by running `sudo visudo` and adding at the end:
>
> ```
> your_username ALL=(ALL) NOPASSWD: /usr/bin/papirus-folders
> ```

</details>

## Installation

### Arch linux

- Download the PKGBUILD
- Run `makepkg -si`

### Manual installation

- Install all [dependencies](#dependencies) (e.g. via an AUR helper like `yay`)
- Clone the repo
- `cd` into the repo root
- Build the wheel with Python
- Install the wheel
- Copy the Fish completions to your Fish completions directory

```sh
yay -S libnotify swappy hyprshot dart-sass app2unit wl-clipboard slurp gpu-screen-recorder glib2 cliphist fuzzel python-build python-installer python-hatch python-hatch-vcs
git clone https://github.com/caelestia-dots/cli.git
cd cli
python -m build --wheel
sudo python -m installer dist/*.whl
sudo cp completions/caelestia.fish /usr/share/fish/vendor_completions.d/caelestia.fish
```

## Usage

All subcommands/options can be explored via the help flag.

```
$ caelestia -h
usage: caelestia [-h] [-v] COMMAND ...

Main control script for the Caelestia dotfiles

options:
  -h, --help     show this help message and exit
  -v, --version  print the current version

subcommands:
  valid subcommands

  COMMAND        the subcommand to run
    shell        start or message the shell
    toggle       toggle a special workspace
    scheme       manage the colour scheme
    screenshot   take a screenshot
    record       start a screen recording
    clipboard    open clipboard history
    emoji        emoji/glyph utilities
    wallpaper    manage the wallpaper
    resizer      window resizer daemon
```

## Configuring

All configuration options are in `~/.config/caelestia/cli.json`.

<details><summary>Example configuration</summary>

```json
{
    "record": {
        "extraArgs": []
    },
    "wallpaper": {
        "postHook": "echo $WALLPAPER_PATH"
    },
    "theme": {
        "enableTerm": true,
        "enableHypr": true,
        "enableDiscord": true,
        "enableSpicetify": true,
        "enableFuzzel": true,
        "enableBtop": true,
        "enableGtk": true,
        "enableQt": true
    },
    "toggles": {
        "communication": {
            "discord": {
                "enable": true,
                "match": [{ "class": "discord" }],
                "command": ["discord"],
                "move": true
            },
            "whatsapp": {
                "enable": true,
                "match": [{ "class": "whatsapp" }],
                "move": true
            }
        },
        "music": {
            "spotify": {
                "enable": true,
                "match": [{ "class": "Spotify" }, { "initialTitle": "Spotify" }, { "initialTitle": "Spotify Free" }],
                "command": ["spicetify", "watch", "-s"],
                "move": true
            },
            "feishin": {
                "enable": true,
                "match": [{ "class": "feishin" }],
                "move": true
            }
        },
        "sysmon": {
            "btop": {
                "enable": true,
                "match": [{ "class": "btop", "title": "btop", "workspace": { "name": "special:sysmon" } }],
                "command": ["foot", "-a", "btop", "-T", "btop", "fish", "-C", "exec btop"]
            }
        },
        "todo": {
            "todoist": {
                "enable": true,
                "match": [{ "class": "Todoist" }],
                "command": ["todoist"],
                "move": true
            }
        }
    }
}
```

</details>
