#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Check for the file argument
if [ -z "$1" ]; then
    echo "🚨 Error: Please provide the path to the file to be served."
    echo "Usage: $0 <filepath>"
    exit 1
fi

FILE_TO_SERVE="$1"

# Check if the file exists
if [ ! -f "$FILE_TO_SERVE" ]; then
    echo "🚨 Error: File not found at '$FILE_TO_SERVE'"
    exit 1
fi

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🔥 Starting the server to serve lines from '$FILE_TO_SERVE'..."
echo "👉 Access the API at http://127.0.0.1:8000/lines/<line_index>"

# Export the filename as an environment variable and run the server
# Uvicorn is a lightning-fast ASGI server, perfect for our needs.
export FILE_TO_SERVE
uvicorn line_server.main:app --host 0.0.0.0 --port 8000
