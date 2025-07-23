#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting build process..."

# Check if python3 is available
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

# Create a Python virtual environment to isolate dependencies
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install required packages from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✅ Build complete. Environment is ready."
