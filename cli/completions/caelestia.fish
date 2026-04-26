set -l seen '__fish_seen_subcommand_from'
set -l has_opt '__fish_contains_opt'

set -l commands shell toggle scheme screenshot record clipboard emoji-picker wallpaper resizer
set -l not_seen "not $seen $commands"

# Disable file completions
complete -c caelestia -f

# Add help for any command
complete -c caelestia -s 'h' -l 'help' -d 'Show help'

# Subcommands
complete -c caelestia -n $not_seen -a 'shell' -d 'Start the shell or message it'
complete -c caelestia -n $not_seen -a 'toggle' -d 'Toggle a special workspace'
complete -c caelestia -n $not_seen -a 'scheme' -d 'Manage the colour scheme'
complete -c caelestia -n $not_seen -a 'screenshot' -d 'Take a screenshot'
complete -c caelestia -n $not_seen -a 'record' -d 'Start a screen recording'
complete -c caelestia -n $not_seen -a 'clipboard' -d 'Open clipboard history'
complete -c caelestia -n $not_seen -a 'emoji' -d 'Emoji/glyph utilities'
complete -c caelestia -n $not_seen -a 'wallpaper' -d 'Manage the wallpaper'
complete -c caelestia -n $not_seen -a 'resizer' -d 'Window resizer'

# Shell
set -l commands mpris drawers wallpaper notifs
set -l not_seen "$seen shell && not $seen $commands"
complete -c caelestia -n $not_seen -s 's' -l 'show' -d 'Print all IPC commands'
complete -c caelestia -n $not_seen -a 'mpris' -d 'Mpris control'
complete -c caelestia -n $not_seen -a 'drawers' -d 'Toggle drawers'
complete -c caelestia -n $not_seen -a 'wallpaper' -d 'Wallpaper control (for internal use)'
complete -c caelestia -n $not_seen -a 'notifs' -d 'Notification control'

set -l commands getActive play pause playPause stop next previous list
set -l not_seen "$seen shell && $seen mpris && not $seen $commands"
complete -c caelestia -n $not_seen -a 'play' -d 'Play media'
complete -c caelestia -n $not_seen -a 'pause' -d 'Pause media'
complete -c caelestia -n $not_seen -a 'playPause' -d 'Play/pause media'
complete -c caelestia -n $not_seen -a 'next' -d 'Skip to next song'
complete -c caelestia -n $not_seen -a 'previous' -d 'Go to previous song'
complete -c caelestia -n $not_seen -a 'stop' -d 'Stop media'
complete -c caelestia -n $not_seen -a 'list' -d 'List media players'
complete -c caelestia -n $not_seen -a 'getActive' -d 'Get a property from the active MPRIS player'

set -l commands trackTitle trackArtist trackAlbum position length identity
set -l not_seen "$seen shell && $seen mpris && $seen getActive && not $seen $commands"
complete -c caelestia -n $not_seen -a 'trackTitle' -d 'Track title'
complete -c caelestia -n $not_seen -a 'trackArtist' -d 'Track artist'
complete -c caelestia -n $not_seen -a 'trackAlbum' -d 'Track album'
complete -c caelestia -n $not_seen -a 'position' -d 'Track position'
complete -c caelestia -n $not_seen -a 'length' -d 'Track length'
complete -c caelestia -n $not_seen -a 'identity' -d 'Player identity'

set -l commands list toggle
set -l not_seen "$seen shell && $seen drawers && not $seen $commands"
complete -c caelestia -n $not_seen -a 'list' -d 'List togglable drawers'
complete -c caelestia -n $not_seen -a 'toggle' -d 'Toggle a drawer'

set -l commands (caelestia shell drawers list 2> /dev/null)
complete -c caelestia -n "$seen shell && $seen drawers && $seen toggle && not $seen $commands" -a "$commands" -d 'drawer'

set -l commands list get set
set -l not_seen "$seen shell && $seen wallpaper && not $seen $commands"
complete -c caelestia -n $not_seen -a 'list' -d 'List wallpapers'
complete -c caelestia -n $not_seen -a 'get' -d 'Get current wallpaper path'
complete -c caelestia -n $not_seen -a 'set' -d 'Change wallpaper'
complete -c caelestia -n "$seen shell && $seen wallpaper && $seen set" -F

complete -c caelestia -n "$seen shell && $seen notifs && not $seen clear" -a 'clear' -d 'Clear popup notifications'

# Toggles
set -l commands communication music specialws sysmon todo notes
complete -c caelestia -n "$seen toggle && not $seen drawers && not $seen $commands" -a "$commands" -d 'toggle'


# -- helpers for dynamic "scheme" completions -------------------------------
function __caelestia_list_names
    caelestia scheme list --names 2>/dev/null
end

function __caelestia_optval --argument opt
    # Return the value for a long option like --name or --flavour
    set -l toks (commandline -opc)
    for i in (seq (count $toks))
        set -l t $toks[$i]
        if string match -q -- "$opt=*"
            string split -m1 -f2 '=' -- $t
            return
        end
        if test "$t" = "$opt"
            if test (math $i + 1) -le (count $toks)
                set -l nxt $toks[(math $i + 1)]
                if not string match -q -- '--*' "$nxt"
                    echo $nxt
                end
            end
            return
        end
    end
end

function __caelestia_list_flavours
    set -l nm (__caelestia_optval --name)
    if test -n "$nm"
        caelestia scheme list --flavours $nm 2>/dev/null
    end
end

function __caelestia_list_modes
    set -l nm (__caelestia_optval --name)
    set -l fl (__caelestia_optval --flavour)
    if test -n "$nm" -a -n "$fl"
        caelestia scheme list --modes $nm $fl 2>/dev/null
    else if test -n "$nm"
        caelestia scheme list --modes $nm 2>/dev/null
    else
        caelestia scheme list --modes 2>/dev/null
    end
end

function __caelestia_list_variants
    caelestia scheme list --variants 2>/dev/null
end
# --------------------------------------------------------------------------

# Scheme
set -l commands list get set
set -l not_seen "$seen scheme && not $seen $commands"
complete -c caelestia -f -n $not_seen -a 'list' -d 'List available schemes'
complete -c caelestia -f -n $not_seen -a 'get' -d 'Get scheme properties'
complete -c caelestia -f -n $not_seen -a 'set' -d 'Set the current scheme'

# scheme list
complete -c caelestia -f -n "$seen scheme && $seen list" -l 'names'    -d 'List scheme names'
complete -c caelestia -f -n "$seen scheme && $seen list" -l 'flavours' -d 'List scheme flavours' -r -a '(__caelestia_list_names)'
complete -c caelestia -f -n "$seen scheme && $seen list" -l 'modes'    -d 'List modes (optional NAME [FLAVOUR])'
complete -c caelestia -f -n "$seen scheme && $seen list" -l 'variants' -d 'List scheme variants'
complete -c caelestia -f -n "$seen scheme && $seen list" -l 'json'     -d 'Output JSON'

# scheme set
complete -c caelestia -f -n "$seen scheme && $seen set" -l 'notify' -d 'Send a notification after applying'
complete -c caelestia -f -n "$seen scheme && $seen set" -l 'random' -d 'Switch to a random scheme'

complete -c caelestia -f -n "$seen scheme && $seen set" -l 'name'    -d 'Set scheme name'    -r -a '(__caelestia_list_names)'
complete -c caelestia -f -n "$seen scheme && $seen set" -l 'flavour' -d 'Set scheme flavour' -r -a '(__caelestia_list_flavours)'
complete -c caelestia -f -n "$seen scheme && $seen set" -l 'mode'    -d 'Set scheme mode'    -r -a '(__caelestia_list_modes)'
complete -c caelestia -f -n "$seen scheme && $seen set" -l 'variant' -d 'Set scheme variant' -r -a '(__caelestia_list_variants)'

# Screenshot
complete -c caelestia -n "$seen screenshot" -s 'r' -l 'region' -d 'Capture region'
complete -c caelestia -n "$seen screenshot" -s 'f' -l 'freeze' -d 'Freeze while selecting region'

# Record
complete -c caelestia -n "$seen record" -s 'r' -l 'region' -d 'Capture region'
complete -c caelestia -n "$seen record" -s 's' -l 'sound' -d 'Capture sound'

# Clipboard
complete -c caelestia -n "$seen clipboard" -s 'd' -l 'delete' -d 'Delete from cliboard history'

# Wallpaper
complete -c caelestia -n "$seen wallpaper" -s 'p' -l 'print' -d 'Print the scheme for a wallpaper' -rF
complete -c caelestia -n "$seen wallpaper" -s 'r' -l 'random' -d 'Switch to a random wallpaper' -rF
complete -c caelestia -n "$seen wallpaper" -s 'f' -l 'file' -d 'The file to switch to' -rF
complete -c caelestia -n "$seen wallpaper" -s 'n' -l 'no-filter' -d 'Do not filter by size'
complete -c caelestia -n "$seen wallpaper" -s 't' -l 'threshold' -d 'The threshold to filter by' -r
complete -c caelestia -n "$seen wallpaper" -s 'N' -l 'no-smart' -d 'Disable smart mode switching'

# Emoji
complete -c caelestia -n "$seen emoji" -s 'p' -l 'picker' -d 'Open emoji/glyph picker'
complete -c caelestia -n "$seen emoji" -s 'f' -l 'fetch' -d 'Fetch emoji/glyph data from remote'

# Resizer
complete -c caelestia -n "$seen resizer" -s 'd' -l 'daemon' -d 'Start in daemon mode'
complete -c caelestia -n "$seen resizer" -a 'pip' -d 'Quick pip mode'
complete -c caelestia -n "$seen resizer" -a 'active' -d 'Select the active window'
