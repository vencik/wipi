#!/bin/sh

proc=4
socket="/var/tmp/wipi.sock"

this=$(realpath "$0" | xargs basename)
this_dir=$(realpath "$0" | xargs dirname)
wipi_dir=$(realpath "$this_dir/../")
venv_dir="$wipi_dir/.venv"


usage() {
    cat <<HERE
Usage: $this [OPTIONS]

OPTIONS:
    -h or --help                Display this help and exit
    -p or --processes N         Number of uWSGI workers (default: $proc)

HERE
}

# Parse options
eval set -- "$(getopt -o hp: -l help,processes: -- "$@")"
while test "$1" != "--"; do
    case "$1" in
    -h|--help) usage; exit 0;;

    -p|--processes) shift; proc=$1;;
    esac
    shift
done
shift  # shift the final "--"

# Run application server
PATH="$venv_dir/bin:$PATH" uwsgi --need-app \
    --processes "$proc" \
    --plugin python3 \
    --socket "$socket" \
    --chmod-socket=666 \
    --manage-script-name \
    --mount /wipi/api=wipi.api:app \
    --python-path "$wipi_dir" \
    --virtualenv "$venv_dir" \
    --pyargv "$wipi_dir/etc/config.json"
