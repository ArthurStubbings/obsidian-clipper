# Obsidian Clipper

Clip YouTube videos and Instagram Reels into structured Obsidian markdown notes with one keyboard shortcut.

- Grabs the current Safari URL via AppleScript
- Fetches the full transcript (YouTube API or Whisper for Reels)
- Classifies the video (reference, tutorial, essay) and picks the right note format
- Sends it to Claude to generate a concise, opinionated note
- Cross-links to existing notes already in your vault
- Writes the `.md` file directly into your Obsidian vault
- Shows a macOS notification on success

YouTube runs in under 10 seconds. Instagram Reels take 30–60 seconds (local Whisper transcription) and notify you when done.

## Note formats

The tool detects the video type and generates a format-appropriate note:

**Reference** (list of N things) — enumerates every item with its own section, plus top picks  
**Tutorial** — captures the skill being taught, not the demo project; numbered steps + gotchas  
**Essay** — summary bullets, key idea, and actions

Every note includes YAML frontmatter compatible with Obsidian Dataview, and Related notes links are chosen from notes that already exist in your vault.

## Requirements

- macOS (AppleScript + notification support)
- Safari as primary browser
- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) — required for Instagram Reels (`brew install ffmpeg`)
- Anthropic API key

## Setup

```bash
git clone https://github.com/ArthurStubbings/obsidian-clipper
cd obsidian-clipper
bash setup.sh
```

Then:

1. Edit `.env` and set your API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
2. Edit `config.yaml` and set your vault path:
   ```yaml
   vault:
     path: ~/Documents/Obsidian/YourVaultName
     subfolder: Sources
   ```
   Find your vault name at: `~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/`

## Test it

```bash
source venv/bin/activate
python clip.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Keyboard shortcut (Raycast)

1. In Raycast go to **Extensions → Script Commands → Add Directories** and point it at the `obsidian-clipper` folder — Raycast will pick up `raycast-clip.sh` automatically
2. Find `Obsidian Clipper` in Raycast, click the hotkey field, and assign `⌘⇧O`

Raycast returns instantly for both YouTube and Reels. For Reels, a macOS notification appears when the note is saved. If something goes wrong, check `/tmp/obsidian-clipper.log`.

## Keyboard shortcut (Automator)

1. Open **Automator** → New Document → **Quick Action**
2. Set "Workflow receives" to **no input** in **any application**
3. Add a **Run Shell Script** action with Shell set to `/bin/zsh`:
   ```bash
   nohup /path/to/obsidian-clipper/venv/bin/python /path/to/obsidian-clipper/clip.py > /tmp/obsidian-clipper.log 2>&1 &
   ```
4. Save as `Obsidian Clipper`
5. Go to **System Settings → Keyboard → Keyboard Shortcuts → Services** → find `Obsidian Clipper` → assign `⌘⇧O`

## Supported URLs

| Platform | URL formats |
|---|---|
| YouTube | `youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/shorts/...` |
| Instagram | `instagram.com/reel/...`, `instagram.com/reels/...`, `instagram.com/p/...` |

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1a | YouTube → macOS Safari → Obsidian | ✅ Done |
| 1b | Instagram Reels support | ✅ Done |
| 1c | Polish, README, public v1.0 | ✅ Done |
| 2 | iOS share sheet via Shortcuts + webhook | Planned |
| 3 | Articles, podcasts, tweets | Planned |

## License

MIT
