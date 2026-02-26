#!/usr/bin/env python3
"""
Claude Code Notifier - desktop notification hook with AI session summary.
Supports macOS (osascript) and Windows (PowerShell toast).

Triggers on:
  - Stop: Claude finished responding
  - Notification: Claude needs user input or permission
"""

import json
import sys
import os
import subprocess
import re


def get_first_user_message(transcript_path):
    """Extract the first user message from a Claude Code transcript JSONL file."""
    try:
        with open(transcript_path, "r") as f:
            for line in f:
                obj = json.loads(line.strip())
                if obj.get("type") == "user" and obj.get("message", {}).get("role") == "user":
                    content = obj["message"].get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            b.get("text", "") for b in content if b.get("type") == "text"
                        )
                    return content.strip().replace("\n", " ")[:200]
    except Exception:
        pass
    return ""


def summarize_with_ai(text, base_url, auth_token):
    """Use Anthropic API (claude-3-haiku) to generate a short session summary."""
    try:
        import anthropic

        client = anthropic.Anthropic(base_url=base_url, auth_token=auth_token)
        resp = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": f"Summarize the task in 6 words or less. Output only the summary, no punctuation or quotes:\n{text}"
            }]
        )
        return resp.content[0].text.strip().strip("\"'、。！.,!\"'")
    except Exception:
        return ""


def summarize_locally(text):
    """Extract a short key phrase from the text without any API call."""
    # Strip common Chinese prefixes
    text = re.sub(
        r'^(请你?|帮我|帮忙|麻烦你?|我想要?|我要|我需要|我希望|能不能|可以|能否|你能|我的)+',
        '', text
    )
    # Split into clauses
    parts = re.split(r'[，。！？,.?;；：:\n]', text)
    parts = [p.strip() for p in parts if len(p.strip()) >= 2]
    if not parts:
        return text[:12]

    # Score clauses: prefer short, early ones
    scored = []
    for i, p in enumerate(parts):
        score = (1.0 / (i + 1)) * (1.0 / max(len(p), 1))
        if 4 <= len(p) <= 12:
            score *= 3
        scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1]

    # Truncate: word-boundary for English, char-boundary for CJK
    if re.search(r'[a-zA-Z]', best):
        words = best.split()
        result = ''
        for w in words:
            if len(result + ' ' + w) > 16:
                break
            result = (result + ' ' + w).strip()
        return result or best[:12]
    return best[:12]


def get_session_name(transcript, session_id, cwd):
    """Get a short session name: cache -> AI summary -> local extraction -> dir name."""
    if sys.platform == "win32":
        cache_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "claude-code-notifier")
    else:
        cache_dir = os.path.expanduser("~/.cache/claude-code-notifier")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, session_id) if session_id else ""

    # 1. Check cache
    if cache_file and os.path.exists(cache_file):
        with open(cache_file) as f:
            name = f.read().strip()
            if name:
                return name

    # 2. Generate from transcript
    first_msg = get_first_user_message(transcript) if transcript else ""
    session_name = ""

    if first_msg:
        # Try AI summary
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
        auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")

        if base_url and (auth_token or api_key):
            session_name = summarize_with_ai(
                first_msg, base_url, auth_token or api_key
            )
        elif api_key:
            session_name = summarize_with_ai(
                first_msg, "https://api.anthropic.com", api_key
            )

        # Fallback: local extraction
        if not session_name:
            session_name = summarize_locally(first_msg)

    # Write cache
    if session_name and cache_file:
        with open(cache_file, "w") as f:
            f.write(session_name)

    return session_name or os.path.basename(cwd)


WINDOWS_SOUNDS = {
    "Hero": r"C:\Windows\Media\Windows Notify System Generic.wav",
    "Sosumi": r"C:\Windows\Media\Windows Notify Calendar.wav",
}


def send_notification(title, subtitle, body, sound):
    """Send a desktop notification with sound (macOS or Windows)."""
    if sys.platform == "win32":
        _send_windows_notification(title, subtitle, body, sound)
    else:
        _send_macos_notification(title, subtitle, body, sound)


def _send_macos_notification(title, subtitle, body, sound):
    """Send a macOS desktop notification with sound."""
    body = body.replace('"', '\\"')
    subtitle = subtitle.replace('"', '\\"')
    script = (
        f'display notification "{body}" '
        f'with title "{title}" '
        f'subtitle "{subtitle}" '
        f'sound name "{sound}"'
    )
    subprocess.run(["osascript", "-e", script], capture_output=True)


def _send_windows_notification(title, subtitle, body, sound):
    """Send a Windows toast notification with sound."""
    sound_path = WINDOWS_SOUNDS.get(sound, "")
    # Play sound in background
    if sound_path and os.path.exists(sound_path):
        ps_sound = (
            f"(New-Object System.Media.SoundPlayer '{sound_path}').PlaySync()"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_sound],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    # Send toast notification via PowerShell with registered App ID
    display_body = f"{subtitle}\n{body}" if subtitle else body
    title = title.replace("'", "''")
    display_body = display_body.replace("'", "''")
    ps_toast = f"""
$appId = 'Claude.Code.Notifier'
$regPath = 'HKCU:\\Software\\Classes\\AppUserModelId\\' + $appId
if (-not (Test-Path $regPath)) {{
    New-Item -Path $regPath -Force | Out-Null
    New-ItemProperty -Path $regPath -Name 'DisplayName' -Value 'Claude Code' -PropertyType String -Force | Out-Null
}}
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
$xml = @'
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{title}</text>
      <text>{display_body}</text>
    </binding>
  </visual>
</toast>
'@
$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$toast = [Windows.UI.Notifications.ToastNotification]::new($doc)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_toast],
        capture_output=True,
    )


def main():
    data = json.loads(os.environ.get("HOOK_INPUT", "{}"))
    event = data.get("hook_event_name", "")

    if event not in ("Stop", "Notification"):
        sys.exit(0)

    cwd = data.get("cwd", "")
    session_id = data.get("session_id", "")
    transcript = data.get("transcript_path", "")
    last_msg = data.get("last_assistant_message", "")[:80].replace('"', "").replace("\n", " ")
    notif_msg = data.get("message", "").replace('"', "").replace("\n", " ")

    session_name = get_session_name(transcript, session_id, cwd)

    if event == "Stop":
        send_notification(
            title="✅ 已完成",
            subtitle=session_name,
            body=last_msg or "回复已完成",
            sound="Hero"
        )
    else:
        send_notification(
            title="⏳ 等待操作",
            subtitle=session_name,
            body=notif_msg or "需要你的输入",
            sound="Sosumi"
        )


if __name__ == "__main__":
    main()
