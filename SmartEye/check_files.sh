#!/bin/bash

# Get the directory of the currently executing script
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Specify the directory to monitor
directory_to_monitor="$script_dir/captured/video"

# Extensions to check for
extensions=("mp4" "avi" "mkv" "mpeg4")

while true; do
    # Get the list of files with specified extensions in the main directory (not subdirectories)
    files=$(find "$directory_to_monitor" -maxdepth 1 -type f \( -iname "*.mp4" -o -iname "*.avi" -o -iname "*.mkv" -o -iname "*.mpeg4" \))

    # Iterate through the files
    for file in $files; do
        echo "New file added: $file"
        
        # Trigger the Python script with the new file path as an argument
        python "$script_dir/src/gemini_pred.py" "$file"
    done

    # Wait for 1 minute before checking again
    sleep 60
done
