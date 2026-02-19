#!/bin/bash
# Claude Code Notifier - hook entry point
# Reads JSON from stdin and delegates to notify.py

export HOOK_INPUT=$(cat)

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Auto-detect Python 3
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    # Fallback: basic notification without AI summary
    osascript -e 'display notification "Claude Code needs attention" with title "Claude Code" sound name "Hero"'
    exit 0
fi

exec "$PYTHON" "$SCRIPT_DIR/notify.py"
