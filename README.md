# Obsidian Clipper

Clip YouTube videos (and Instagram Reels) into structured Obsidian markdown notes with one keyboard shortcut.

- Grabs the current Safari URL via AppleScript
- Fetches the full transcript (YouTube API or Whisper for Reels)
- Sends it to Claude to generate a concise, opinionated note
- Writes the `.md` file directly into your Obsidian vault
- Shows a macOS notification on success

The whole pipeline runs in under 10 seconds for most YouTube videos.

## Generated note format

```markdown
---
title: How to Build a Sustainable Morning Routine
source: https://youtube.com/watch?v=...
platform: YouTube
creator: Channel Name
date_saved: 2026-04-28
duration: 12 min
tags: [habit-design, morning-routine, productivity, behaviour-change]
status: inbox
---

## Summary
- ...

## Key idea
...

## Actions
- [ ] ...

## Related notes
- [[Habit Formation]]

## Source
[View original](https://youtube.com/watch?v=...)
```

## Requirements

- macOS (AppleScript + notification support)
- Safari as primary browser
- Python 3.11+
- Anthropic API key

## Setup

```bash
git clone https://github.com/your-username/obsidian-clipper
cd obsidian-clipper
bash setup.sh
```

Then:

1. Edit `.env` and set `ANTHROPIC_API_KEY=sk-ant-...`
2. Edit `config.yaml` and set `vault.path` to your Obsidian vault folder

## Usage

```bash
source venv/bin/activate

# Clip the current Safari tab
python clip.py

# Clip an explicit URL (useful for testing)
python clip.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Verbose output
python clip.py --debug
```

## Keyboard shortcut (macOS Automator)

1. Open **Automator** → New Document → **Quick Action**
2. Set "Workflow receives" to **no input** in **any application**
3. Add a **Run Shell Script** action:
   ```bash
   cd /path/to/obsidian-clipper
   source venv/bin/activate
   python clip.py
   ```
4. Save as `Obsidian Clipper`
5. Go to **System Settings → Keyboard → Keyboard Shortcuts → Services** and assign `⌘⇧O`

## Keyboard shortcut (Raycast)

Create a Script Command pointing to:
```bash
#!/usr/bin/env bash
cd /path/to/obsidian-clipper
source venv/bin/activate
python clip.py
```

## Instagram Reels support

Reels transcription uses `yt-dlp` + `openai-whisper` and runs locally — no extra API keys needed. It's slower than YouTube (30–60 s depending on video length and your machine). yt-dlp may require cookies for some Reels; see [yt-dlp docs](https://github.com/yt-dlp/yt-dlp#usage) for details.

## Roadmap

| Phase | Scope |
|-------|-------|
| 1a | YouTube → macOS Safari → Obsidian (this release) |
| 1b | Instagram Reels support |
| 1c | Config polish, error handling, public v1.0 |
| 2 | iOS share sheet via Shortcuts + webhook |
| 3 | Articles, podcasts, tweets |

## License

MIT
