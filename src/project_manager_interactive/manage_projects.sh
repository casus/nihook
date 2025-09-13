#!/bin/bash

# Get current directory (volume folder)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "$DIR"

# Call the Python script and pass the volume folder path
python3 ../../src/project_manager_interactive/manage_projects.py "$DIR"