#!/bin/bash

# check if the docker command exists and is functional
check_docker_command() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker command not found. Please install Docker and try again."
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running or cannot be accessed. Please ensure Docker is properly installed and running."
    exit 1
  fi

  echo "Docker is installed and running: proceeding"
}

# this function is the first step - check if docker exists/running before proceeding
check_docker_command

# globals
BRANCH="main"
YEAR=$(date +"%Y")

# directory setup
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
BASE_DIR="$SCRIPT_DIR/.."
OUTPUT_DIR="$BASE_DIR/output"

# docker setup
DOCKER_CONTAINER_NAME="afl-parity-container"
DOCKER_COMPOSE_FILE="$BASE_DIR/docker-compose.yml"

# logging setup
CURRENT_DATE=$(date +"%Y%m%d")
CURRENT_TIME=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="$BASE_DIR/.logs"
LOG_DIR_DT="$LOG_DIR/$CURRENT_DATE"
LOG_FILE="$LOG_DIR_DT/${CURRENT_TIME}_${YEAR}_run_docker.log"

log_with_datetime() {
  local level="$1"
  local message="$2"
  local current_datetime=$(date +"%Y-%m-%d %H:%M:%S")
  echo "[$current_datetime][$level] $message" | tee -a "$LOG_FILE"
}

# ensure log directory exists
if ! mkdir -p "$LOG_DIR_DT"; then
  echo "ERROR" "Failed to create log directory: $LOG_DIR_DT."
  exit 1
fi

# ensure log ownership
touch "$LOG_FILE" # empty logfile
CURRENT_USER=$(whoami)
chown "$CURRENT_USER:$CURRENT_USER" "$LOG_FILE" 2>/dev/null || log_with_datetime "WARN" "Unable to set ownership for $LOG_FILE."

# ensure output directory exists
if ! mkdir -p "$OUTPUT_DIR"; then
  log_with_datetime "ERROR" "Failed to create output directory: $OUTPUT_DIR."
  exit 1
fi

push_to_github() {
  cd "$BASE_DIR" || exit
  # check for changes before/after adding files
  git checkout $BRANCH
  git pull origin $BRANCH
  STATUS_BEFORE=$(git status --porcelain)
  git add "$OUTPUT_DIR/"
  STATUS_AFTER=$(git status --porcelain)

  if [ "$STATUS_BEFORE" != "$STATUS_AFTER" ]; then
    if check_first_hamiltonian_cycle_already_exists; then
      git commit -m "feed: automated push - hamiltonian cycle found for $YEAR"
    else
      git commit -m "feed: automated push for $YEAR traversal"
    fi
    git push origin "$BRANCH"
    log_with_datetime "INFO" "Pushed git commit to $BRANCH."
  else
    log_with_datetime "INFO" "No changes detected to output, skipping commit/push."
  fi
}

check_first_hamiltonian_cycle_already_exists() {
  FILE_PATH="$OUTPUT_DIR/${YEAR}_dfs_traversal_output.json"
  
  # check if file exists and inspect if a Hamiltonian cycle is present
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
  log_with_datetime "INFO" "First Hamiltonian Cycle already found, no need to run."
else
  log_with_datetime "INFO" "No Hamiltonian Cycle for $YEAR yet found - proceeding."

  status=$(check_container_status)
  
  if [ "$status" = "not_exists" ]; then
    log_with_datetime "INFO" "Building Docker image..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build
  fi

  if [ "$status" = "running" ]; then
    log_with_datetime "INFO" "Container is running from a previous execution, skipping."
  else
    # not_exists or exists - lets go (as not_exists will have run docker build up above)
    docker-compose -f "$DOCKER_COMPOSE_FILE" up | tee -a "$LOG_FILE"
    # push any results
    push_to_github
    # log completion
    log_with_datetime "INFO" "Completed run."
  fi  
fi