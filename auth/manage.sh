#!/bin/bash

# Get current directory (volume folder)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "$DIR"

# Call the Python script and pass the volume folder path
python3 ../../datalad_automation/auth/manage_users.py "$DIR"
