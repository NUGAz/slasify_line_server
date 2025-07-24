#!/bin/bash
set -e

# Use the first argument as the source file, or default to 'test_file.txt'
export SOURCE_FILE=${1:-test_file.txt}

# Check if the source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "🚨 Error: File not found at '$SOURCE_FILE'"
    exit 1
fi

sudo systemctl is-active --quiet docker || {
  echo "🚨 Docker service is not running. Please start it with 'sudo systemctl start docker'" >&2;
  exit 1;
}

echo "🔥 Starting server for file: $SOURCE_FILE..."
echo "👉 Access the API at http://localhost:8000/lines/<line_index>"
echo "ℹ️  Press Ctrl+C to stop the server."

# Add the -E flag here to preserve the SOURCE_FILE variable
sudo -E docker compose up --build
