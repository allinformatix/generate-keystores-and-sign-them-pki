#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3 before proceeding."
    exit 1
fi

# Check the Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ "$PYTHON_VERSION" < "3" ]]; then
    echo "You need Python 3 or higher. Current version is $PYTHON_VERSION."
    exit 1
else
    echo "Python 3 is installed. Version: $PYTHON_VERSION"
fi

# Create a virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Install necessary dependencies
if [ ! -f "requirements.txt" ]; then
    echo "Creating requirements.txt..."
    echo "PyYAML" > requirements.txt  # Add PyYAML as a dependency
fi

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify that PyYAML is installed
if python -c "import yaml" &> /dev/null; then
    echo "PyYAML installed successfully."
else
    echo "Failed to install PyYAML."
    exit 1
fi

# Verify that standard libraries are available
echo "Checking standard libraries..."
python -c "import os, subprocess, shutil, datetime, tempfile, glob" &> /dev/null

if [ $? -eq 0 ]; then
    echo "All required standard libraries are available."
else
    echo "Error: One or more standard libraries are missing."
    exit 1
fi

echo "Setup complete. Virtual environment is active."
