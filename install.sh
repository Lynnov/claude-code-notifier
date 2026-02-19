#!/bin/bash
# Claude Code Notifier - Installer
# Installs the notification hook into Claude Code settings

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTIFY_SH="$SCRIPT_DIR/notify.sh"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "🔔 Claude Code Notifier - Installer"
echo ""

# Ensure notify.sh is executable
chmod +x "$NOTIFY_SH"

# Check if settings file exists
if [ ! -f "$SETTINGS_FILE" ]; then
    mkdir -p "$HOME/.claude"
    echo '{}' > "$SETTINGS_FILE"
    echo "Created $SETTINGS_FILE"
fi

# Backup existing settings
cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"
echo "✅ Backed up settings to $SETTINGS_FILE.backup"

# Use Python to merge hooks into settings
python3 -c "
import json, sys

settings_path = '$SETTINGS_FILE'
notify_cmd = '$NOTIFY_SH'

with open(settings_path, 'r') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})

hook_entry = [{
    'hooks': [{'command': notify_cmd, 'type': 'command'}],
    'matcher': '.*'
}]

hooks['Stop'] = hook_entry
hooks['Notification'] = hook_entry

settings['hooks'] = hooks

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print('✅ Hooks installed:')
print('   - Stop       → notification when Claude finishes responding')
print('   - Notification → notification when Claude needs your input')
"

echo ""
echo "🎉 Installation complete! Restart Claude Code to activate."
echo ""
echo "Optional: Install 'anthropic' Python package for AI-powered session summaries:"
echo "   pip install anthropic"
