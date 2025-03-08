#!/bin/bash

# Define the API endpoint
API_URL="https://api.squiggle.com.au/sse/test"
# REPO_PATH="/path/to/your/repo"  # Path to your local GitHub repository
# BRANCH="main"  # Git branch to push changes
BRANCH="feed"
YEAR=$(date +"%Y")
IMAGE_NAME="afl-parity"
CONTROL_FILE="/tmp/api_feed_control"  # Control file to pause/resume the loop

# Function to push changes to GitHub
push_to_github() {
#   cd "$REPO_PATH"
  git add ./output/$YEAR/*
  git commit -m "feed: match completed for $YEAR"
  git push origin "$BRANCH"
}

# Function to check if "first_hamiltonian_cycle" is null
check_hamiltonian_cycle() {
  FILE_PATH="./output/$YEAR/${YEAR}_dfs_traversal_output.json"
  
  # Check if the JSON file exists
  if [[ -f "$FILE_PATH" ]]; then
    FIRST_HAMILTONIAN_CYCLE=$(jq '.first_hamiltonian_cycle' "$FILE_PATH")
    if [[ "$FIRST_HAMILTONIAN_CYCLE" == "null" ]]; then
      echo "FirstCycleIsNull"
      return 0  # "first_hamiltonian_cycle" is null
    else
      echo "FirstCycleNotNull"
      return 1  # "first_hamiltonian_cycle" is not null
    fi
  else
    echo "JSON file does not exist"
    return 0  # JSON file does not exist
  fi
}

# Function to build the Docker image if it doesn't exist
build_docker_image_if_needed() {
  if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "Docker image not found. Building Docker image..."
    docker-compose build
  else
    echo "Docker image already exists. No need to build."
  fi
}

# Create the control file to allow the loop to run
echo "RUN" > "$CONTROL_FILE"

# Use wget to handle the SSE stream and output the complete events
wget -qO- "$API_URL" | while read -r line; do
  # Check the control file to see if the loop should pause
  if [[ $(cat "$CONTROL_FILE") == "PAUSE" ]]; then
    echo "Pausing API feed loop..."
    while [[ $(cat "$CONTROL_FILE") == "PAUSE" ]]; do
      sleep 1
    done
    echo "Resuming API feed loop..."
  fi

  # Check if the line starts with "data:"
  if [[ "$line" == data:* ]]; then
    PAYLOAD=$(echo "$line" | sed -e 's/data: //')
    echo "Payload: $PAYLOAD"

    # Check the "complete" value and trigger events with text for each value
    # COMPLETE=$(echo "$PAYLOAD" | grep -o '"complete":[0-9]*' | awk -F: '{print $2}')
    COMPLETE=$(echo "$PAYLOAD" | grep -o '"team":[0-9]*' | awk -F: '{print $2}')
    COMPLETE=$((COMPLETE))  # Convert to integer
    # if [[ "$COMPLETE" -eq 100 ]]; then
    if [[ "$COMPLETE" -gt 1 ]]; then
      echo "Special Event Triggered: Complete equals '$COMPLETE'"
      echo "Special text for complete=$COMPLETE"

      # Check if "first_hamiltonian_cycle" is null before running Docker container
      if check_hamiltonian_cycle; then
        echo "Run Docker!"
        # Pause the loop
        echo "PAUSE" > "$CONTROL_FILE"

        # Check if build needed
        build_docker_image_if_needed
        # Trigger the Docker container
        docker-compose up

        # Resume the loop
        echo "RUN" > "$CONTROL_FILE"

        # Push the results to GitHub
        push_to_github
      else
        echo "Skipping Docker container run: 'first_hamiltonian_cycle' is not null or JSON file does not exist"
      fi
    fi
  fi

  # Print a separator after each complete event
  if [[ "$line" == "" ]]; then
    echo "-----------------------------"
  fi
done
