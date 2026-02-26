# Claude Code Notifier - Windows Installer
# Installs the notification hook into Claude Code settings

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NotifySh = "$ScriptDir/notify.sh" -replace '\\', '/'
$SettingsFile = Join-Path $env:USERPROFILE ".claude\settings.json"

Write-Host "Claude Code Notifier - Windows Installer" -ForegroundColor Cyan
Write-Host ""

# Ensure settings directory exists
$settingsDir = Split-Path -Parent $SettingsFile
if (-not (Test-Path $settingsDir)) {
    New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
}

# Create settings file if missing
if (-not (Test-Path $SettingsFile)) {
    '{}' | Set-Content -Path $SettingsFile -Encoding UTF8
    Write-Host "Created $SettingsFile"
}

# Backup existing settings
Copy-Item $SettingsFile "$SettingsFile.backup" -Force
Write-Host "Backed up settings to $SettingsFile.backup" -ForegroundColor Green

# Merge hooks into settings using Python
$pyScript = @"
import json, sys, os

settings_path = os.path.join(os.environ['USERPROFILE'], '.claude', 'settings.json')
notify_cmd = '$NotifySh'

with open(settings_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})

hook_entry = [{
    'hooks': [{'command': notify_cmd, 'type': 'command'}],
    'matcher': '.*'
}]

hooks['Stop'] = hook_entry
hooks['Notification'] = hook_entry
settings['hooks'] = hooks

with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print('Hooks installed:')
print('   - Stop         -> notification when Claude finishes responding')
print('   - Notification -> notification when Claude needs your input')
"@

python -c $pyScript
if ($LASTEXITCODE -ne 0) {
    py -3 -c $pyScript
}

Write-Host ""
Write-Host "Installation complete! Restart Claude Code to activate." -ForegroundColor Green
Write-Host ""
Write-Host "Optional: Install 'anthropic' for AI-powered session summaries:"
Write-Host "   pip install anthropic"
