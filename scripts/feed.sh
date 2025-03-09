#!/bin/bash

# globals
API_URL="https://api.squiggle.com.au/sse/test"
# BRANCH="main"
BRANCH="feed"
YEAR=$(date +"%Y")
IMAGE_NAME="afl-parity"
DOCKERBUILT=false

# logging
CURRENT_TIME=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="./.logs/${CURRENT_TIME}_${YEAR}_feed.log"

# directory management
if [ ! -d "./output" ]; then
  echo "Creating ./output directory..."
  mkdir ./output
fi

if [ ! -d "./.logs" ]; then
  echo "Creating ./.logs directory..."
  mkdir ./.logs
fi

log_with_datetime() {
  local message="$1"
  local current_datetime=$(date +"%Y-%m-%d %H:%M:%S")
  echo "[$current_datetime] $message" | tee -a "$LOG_FILE"
}

push_to_github() {
  # check for changes before/after add
  STATUS_BEFORE=$(git status --porcelain)
  git add ./output/
  STATUS_AFTER=$(git status --porcelain)

  if [[ "$STATUS_BEFORE" != "$STATUS_AFTER" ]]; then
    git commit -m "feed: match completed for $YEAR"
    git push origin "$BRANCH"
    log_with_datetime "pushed git commit to $BRANCH"
  else
    log_with_datetime "no changes detected to output, skipping commit and push"
  fi
}

check_hamiltonian_cycle() {
  FILE_PATH="./output/$YEAR/${YEAR}_dfs_traversal_output.json"
  
  # check if file exists and if so insepct if a hamiltonian cycle is present
  # to prevent pointless traversing again and again...
  if [[ -f "$FILE_PATH" ]]; then
    FIRST_HAMILTONIAN_CYCLE=$(jq '.first_hamiltonian_cycle' "$FILE_PATH")
    if [[ "$FIRST_HAMILTONIAN_CYCLE" == "null" ]]; then
      return 0  # "first_hamiltonian_cycle" is null
    else
      return 1  # "first_hamiltonian_cycle" is not null
    fi
  else
    return 0  # JSON file does not exist
  fi
}

# main loop
wget -q -O- "$API_URL" | while read -r line; do
  # get the "event" line
  if [[ "$line" == event:* ]]; then
    EVENT_TYPE=$(echo "$line" | sed -e 's/event: //')
    log_with_datetime "Event Type: $EVENT_TYPE"
  fi
  
    # check if event:complete
#   if [[ "$EVENT_TYPE" == event:complete ]]; then
  if [[ "$EVENT_TYPE" == event:score ]]; then
    # Read the next lines to get the data payload
    read -r id_line
    read -r data_line

    # insepcting the data_line content
    if [[ "$data_line" == data:* ]]; then
      PAYLOAD=$(echo "$data_line" | sed -e 's/data: //')
      log_with_datetime "Payload: $PAYLOAD"

      # when a game is completed, trigger the script
      COMPLETE=$(echo "$PAYLOAD" | grep -o '"complete":[0-9]*' | awk -F: '{print $2}')
      COMPLETE=$((COMPLETE))  # converts to integer
        # if [[ "$COMPLETE" -eq 100 ]]; then
        if [[ "$COMPLETE" -gt 1 ]]; then
            log_with_datetime "Game completed - running script"

            if check_hamiltonian_cycle; then
                echo "check_hamiltonian_cycle"
                # build before run
                if [ "$DOCKERBUILT" = false ]; then
                    log_with_datetime "Building Docker image..."
                    docker-compose build
                    DOCKERBUILT=true
                fi
                                
                # run via docker
                docker-compose up

                # push any results
                push_to_github

                # log
                log_with_datetime "Completed Run"
            fi
        fi
    fi
  fi
done
