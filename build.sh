#!/bin/bash
set -e

# Check if the Docker daemon is running
# The '||' part runs only if the command on the left fails
sudo systemctl is-active --quiet docker || { 
  echo "🚨 Docker service is not running. Please start it with 'sudo systemctl start docker'" >&2; 
  exit 1; 
}

echo "🚀 Building the Docker image using 'sudo'..."

# Run the docker compose command with sudo to handle permissions
sudo docker compose build

echo "✅ Docker image built successfully."
