# Claude Code Notifier

macOS desktop notifications for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Know when Claude finishes or needs your attention — without watching the terminal.

<p align="center">
  <img src="assets/notify-complete.png" width="360" alt="Task complete notification" />
  &nbsp;&nbsp;
  <img src="assets/notify-waiting.png" width="360" alt="Waiting for input notification" />
</p>

## Features

- **✅ 已完成** — Claude 回复完毕时弹出通知 + 提示音
- **⏳ 等待操作** — Claude 需要权限确认或等待输入时弹出通知 + 提示音
- **AI 会话摘要** — 自动调用 claude-3-haiku 将首条消息总结为 6 字短标题，一眼看出是哪个任务
- **本地 fallback** — 没有 API 时自动切换到本地关键词提取，不依赖网络
- **缓存机制** — 每个 session 只调一次 AI，后续通知瞬间触发

## Notification Events

| Event | Title | Sound | When |
|---|---|---|---|
| `Stop` | ✅ 已完成 | Hero | Claude 完成回复 |
| `Notification` | ⏳ 等待操作 | Sosumi | Claude 需要权限或等待输入 |

## Requirements

- **macOS** (uses `osascript` for native notifications)
- **Python 3.6+**
- **Claude Code** installed and configured

## Installation

```bash
git clone https://github.com/yike-gunshi/claude-code-notifier.git
cd claude-code-notifier
bash install.sh
```

Restart Claude Code after installation.

### Optional: Enable AI Session Summary

Install the Anthropic Python SDK to enable AI-powered session name summaries:

```bash
pip install anthropic
```

The notifier will use your existing Claude Code API credentials (`ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`) automatically. If unavailable, it falls back to local keyword extraction.

## How It Works

```
Claude Code Hook (stdin JSON)
        │
        ▼
   notify.sh (entry point)
        │
        ▼
   notify.py
        │
        ├── Read session transcript
        │       │
        │       ▼
        ├── AI Summary (claude-3-haiku)
        │   or Local keyword extraction
        │       │
        │       ▼
        ├── Cache summary (~/.cache/claude-code-notifier/)
        │
        ▼
   macOS Notification + Sound
```

1. Claude Code triggers the hook with JSON via stdin (contains `session_id`, `transcript_path`, `last_assistant_message`, etc.)
2. The script reads the first user message from the session transcript
3. Generates a short summary (AI or local fallback) and caches it per session
4. Sends a macOS native notification with the summary as subtitle

## Configuration

### Change Notification Sounds

Edit `notify.py` and modify the `sound` values. Available macOS system sounds:

`Basso` `Blow` `Bottle` `Frog` `Funk` `Glass` `Hero` `Morse` `Ping` `Pop` `Purr` `Sosumi` `Submarine` `Tink`

### Manual Hook Configuration

If you prefer to configure hooks manually, add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "command": "/path/to/claude-code-notifier/notify.sh", "type": "command" }
        ],
        "matcher": ".*"
      }
    ],
    "Notification": [
      {
        "hooks": [
          { "command": "/path/to/claude-code-notifier/notify.sh", "type": "command" }
        ],
        "matcher": ".*"
      }
    ]
  }
}
```

## Uninstall

```bash
cd claude-code-notifier
bash uninstall.sh
```

## License

MIT
