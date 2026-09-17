set -l seen '__fish_seen_subcommand_from'
set -l commands start stop restart status list-logs logs
set -l not_seen "not $seen $commands"

# Disable file completion globally. It is re-enabled for the logs target below.
complete -c caelestia-shellctl -f

# Help is accepted globally
complete -c caelestia-shellctl -s h -l help -d 'Show help'
# Subcommands
complete -c caelestia-shellctl -n $not_seen -a start -d 'Start Caelestia'
complete -c caelestia-shellctl -n $not_seen -a stop -d 'Stop Caelestia and archive its log'
complete -c caelestia-shellctl -n $not_seen -a restart -d 'Restart Caelestia'
complete -c caelestia-shellctl -n $not_seen -a status -d 'Show the current Quickshell instance'
complete -c caelestia-shellctl -n $not_seen -a list-logs -d 'List instances and archived logs'
complete -c caelestia-shellctl -n $not_seen -a logs -d 'Show an instance log or an archived .qslog file'

# logs options
complete -c caelestia-shellctl -n "$seen logs" \
    -n '__caelestia_shellctl_logs_state options' \
    -s f -l follow \
    -d 'Continue following the log'

complete -c caelestia-shellctl -n "$seen logs" \
    -n '__caelestia_shellctl_logs_state options' \
    -s t -l log-times \
    -d 'Enable log timestamps'

complete -c caelestia-shellctl -n "$seen logs" \
    -n '__caelestia_shellctl_logs_state options' \
    -s T -l no-log-times \
    -d 'Disable log timestamps'

# Offer instance IDs and archived logs
complete -c caelestia-shellctl \
    -n '__caelestia_shellctl_logs_state target' \
    -a '(__caelestia_shellctl_log_targets)' \
    -d 'Instance ID or log file'


# Return live + dead Quickshell instance IDs
function __caelestia_shellctl_instance_ids
    command qs list \
        -c caelestia \
        --show-dead \
        --json \
        --any-display \
        2>/dev/null |
        string replace \
            --regex \
            --filter \
            '^\s*"id":\s*"([^"]+)".*$' \
            '$1' |
        while read -l id
            printf '%s\tQuickshell instance\n' "$id"
        end
end


# Return archived log paths
function __caelestia_shellctl_archived_logs
    command caelestia-shellctl list-logs 2>/dev/null |
        string replace \
            --regex \
            --filter \
            '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}  (.+\.qslog)$' \
            '$1' |
        while read -l file
            printf '%s\tArchived log\n' (string escape -- "$file")
        end
end


function __caelestia_shellctl_log_targets
    __caelestia_shellctl_instance_ids
    __caelestia_shellctl_archived_logs
end

function __caelestia_shellctl_logs_state --argument-names query
    __fish_seen_subcommand_from logs; or return 1

    set -l tokens (commandline -opc)
    set -l logs_index (contains -i -- logs $tokens); or return 1

    set -e tokens[1..$logs_index]

    set -l parsing_options 1
    set -l have_target 0

    for token in $tokens
        if test $parsing_options -eq 1
            switch $token
                case -f --follow \
                     -t --log-times \
                     -T --no-log-times
                    continue

                case -h --help
                    # Help terminates the command
                    return 1

                case --
                    set parsing_options 0
                    continue

                case '-*'
                    # A completed unknown option makes the command invalid
                    return 1
            end
        end

        if test $have_target -eq 1
            return 1
        end

        set have_target 1
    end

    switch $query
        case options
            test $parsing_options -eq 1

        case target
            test $have_target -eq 0

        case '*'
            return 1
    end
end