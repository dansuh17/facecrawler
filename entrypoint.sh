#!/bin/bash

# tells the script to exit if any subcommand returns a non-zero status
set -e

# runs XVFB in the background, which enables headless FireFox crawling
Xvfb :10 -ac &
export DISPLAY=:10

# accepts next command
$@
