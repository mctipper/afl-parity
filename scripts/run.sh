#!/bin/bash

# default is current year
CURRENT_YEAR=$(date +"%Y")
SEASON=$CURRENT_YEAR
CLEARCACHE=""

# parse bash arguments if provided
while [ "$#" -gt 0 ]; do
    case $1 in
        -s|--season) SEASON="$2"; shift ;;
        -c|--clearcache) CLEARCACHE="--clearcache" ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# run
cd src
python main.py --season "$SEASON" $CLEARCACHE
