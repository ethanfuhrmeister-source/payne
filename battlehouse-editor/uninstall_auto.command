#!/bin/bash
# Turns off automatic rough cuts on this Mac (the Resolve menu item still works).
AGENT="$HOME/Library/LaunchAgents/com.battlehouse.assemble.plist"
launchctl bootout "gui/$(id -u)" "$AGENT" 2>/dev/null
rm -f "$AGENT"
echo "Automatic rough cuts turned off. Press Return to close."
read -r
