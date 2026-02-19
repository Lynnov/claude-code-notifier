#!/bin/bash
# Claude Code Notifier - Uninstaller
# Removes notification hooks from Claude Code settings

set -e

SETTINGS_FILE="$HOME/.claude/settings.json"

echo "🔔 Claude Code Notifier - Uninstaller"
echo ""

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "Settings file not found. Nothing to uninstall."
    exit 0
fi

# Backup
cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"
echo "✅ Backed up settings to $SETTINGS_FILE.backup"

python3 -c "
import json

settings_path = '$SETTINGS_FILE'

with open(settings_path, 'r') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})
removed = []

for key in ['Stop', 'Notification']:
    if key in hooks:
        entries = hooks[key]
        # Only remove entries that contain 'notify.sh'
        remaining = [e for e in entries if not any('notify.sh' in h.get('command', '') for h in e.get('hooks', []))]
        if len(remaining) < len(entries):
            removed.append(key)
        if remaining:
            hooks[key] = remaining
        else:
            del hooks[key]

settings['hooks'] = hooks

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

if removed:
    print('✅ Removed hooks: ' + ', '.join(removed))
else:
    print('No Claude Code Notifier hooks found.')
"

# Clean cache
if [ -d "$HOME/.cache/claude-code-notifier" ]; then
    rm -rf "$HOME/.cache/claude-code-notifier"
    echo "✅ Cleared session summary cache"
fi

echo ""
echo "🎉 Uninstall complete. Restart Claude Code to apply."
