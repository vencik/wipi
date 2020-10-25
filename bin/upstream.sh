#!/bin/sh

socket="/var/tmp/wipi.sock"

this=$(realpath "$0" | xargs basename)
this_dir=$(realpath "$0" | xargs dirname)
wipi_dir=$(realpath "$this_dir/../")
venv_dir="$wipi_dir/.venv"

PATH="$venv_dir/bin:$PATH" uwsgi --need-app \
    --processes 1 \
    --plugin python3 \
    --socket "$socket" \
    --chmod-socket=666 \
    --manage-script-name \
    --mount /wipi/api=wipi.api:app \
    --python-path "$wipi_dir" \
    --virtualenv "$venv_dir" \
    --pyargv "$*"
