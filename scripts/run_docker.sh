#!/bin/bash

# globals
BRANCH="main"
YEAR=$(date +"%Y")
DOCKER_CONTAINER_NAME="afl-parity-container"

# dir
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
BASE_DIR="$SCRIPT_DIR/.."
LOG_DIR="$BASE_DIR/.logs"
OUTPUT_DIR="$BASE_DIR/output"

# logging
CURRENT_TIME=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/${CURRENT_TIME}_${YEAR}_run_docker.log"
log_with_datetime() {
  local message="$1"
  local current_datetime=$(date +"%Y-%m-%d %H:%M:%S")
  echo "[$current_datetime] $message" | tee -a "$LOG_FILE"
}

# directory management
if [ ! -d "$OUTPUT_DIR" ]; then
  log_with_datetime "Creating $OUTPUT_DIR directory..."
  mkdir -p "$OUTPUT_DIR"
fi

if [ ! -d "$LOG_DIR" ]; then
  log_with_datetime "Creating $LOG_DIR directory..."
  mkdir -p "$LOG_DIR"
fi


push_to_github() {
  cd "$BASE_DIR" || exit
  # check for changes before/after add
  git checkout $BRANCH
  git pull origin $BRANCH
  STATUS_BEFORE=$(git status --porcelain)
  git add "$OUTPUT_DIR/"
  STATUS_AFTER=$(git status --porcelain)

  if [[ "$STATUS_BEFORE" != "$STATUS_AFTER" ]]; then
    if check_first_hamiltonian_cycle_already_exists; then
      git commit -m "feed: automated push - hamiltonian cycle found for $YEAR"
    else
      git commit -m "feed: automated push for $YEAR traversal"
    fi
    git push origin "$BRANCH"
    log_with_datetime "pushed git commit to $BRANCH"
  else
    log_with_datetime "no changes detected to output, skipping commit / push"
  fi
}


check_first_hamiltonian_cycle_already_exists() {
  FILE_PATH="$OUTPUT_DIR/${YEAR}_dfs_traversal_output.json"
  
  # check if file exists and if so inspect if a hamiltonian cycle is present
  if [ -f "$FILE_PATH" ]; then
    FIRST_HAMILTONIAN_CYCLE=$(jq '.first_hamiltonian_cycle' "$FILE_PATH")
    if [ "$FIRST_HAMILTONIAN_CYCLE" == "null" ]; then
      return 1  # "first_hamiltonian_cycle" is null
    else
      return 0  # "first_hamiltonian_cycle" is not null
    fi
  else
    return 1  # JSON file does not exist
  fi
}


check_container_status() {
  if docker ps --filter "name=$DOCKER_CONTAINER_NAME" | grep "$DOCKER_CONTAINER_NAME" > /dev/null 2>&1; then
    echo "running"
  elif docker ps -a --filter "name=$DOCKER_CONTAINER_NAME" | grep "$DOCKER_CONTAINER_NAME" > /dev/null 2>&1; then
    echo "exists"
  else
    echo "not_exists"
  fi
}

if check_first_hamiltonian_cycle_already_exists; then
  log_with_datetime "First Hamiltonian Cycle Already found, no need to run"
else
  log_with_datetime "No Hamiltonian Cycle for $YEAR yet found - proceeding"

  status=$(check_container_status)
  
  if [ "$status" = "not_exists" ]; then
    log_with_datetime "Building Docker image..."
    docker-compose build
  fi

  if [ "$status" = "running" ]; then
    echo "Container is running from previous execution, skipping"
  else
    # not_exists or exists - lets go (as not_exists will have run docker build up above)
    docker-compose up | tee -a "$LOG_FILE"
    # push any results
    push_to_github
    # log
    log_with_datetime "Completed Run"
  fi  
fi