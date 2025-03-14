#!/bin/bash

# the script dir, not the dir the script was run from
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# default is current year
CURRENT_YEAR=$(date +"%Y")
SEASON=$CURRENT_YEAR
DEBUG=""

# parse bash arguments if provided
while [ "$#" -gt 0 ]; do
    case $1 in
        -s|--season) SEASON="$2"; shift ;;
        -d|--debug) DEBUG="--DEBUG" ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# run
cd "$SCRIPT_DIR/../src"
uv run --no-dev -q main.py --season "$SEASON" $DEBUG

# universal read/write perms on output
chmod -R ugo+rw /afl-parity/output
