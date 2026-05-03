#!/usr/bin/env python3
"""clip.py — Obsidian Clipper entrypoint.

Usage:
    python clip.py          # clips the current Safari tab
    python clip.py <url>    # clips an explicit URL (for testing)
"""

import argparse
import logging
import subprocess
import sys
import urllib.parse
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

from clipper.claude import generate_note
from clipper.formatter import build_filename
from clipper.safari import Platform, detect_platform, get_safari_url
from clipper.transcript import get_transcript
from clipper.vault import (
    get_existing_sources,
    get_existing_titles,
    send_notification,
    write_note,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as f:
        return yaml.safe_load(f)


def clip(url: str, config: dict, dry_run: bool = False, open_after: bool = False) -> None:
    platform = detect_platform(url)
    if platform == Platform.UNSUPPORTED:
        raise ValueError(
            f"Unsupported URL — only YouTube and Instagram Reels are supported.\nURL: {url}"
        )

    logger.info("Platform detected: %s", platform.value)

    vault_path = config["vault"]["path"]
    subfolder = config["vault"].get("subfolder", "Sources")

    existing_sources = get_existing_sources(vault_path, subfolder=subfolder)
    if url in existing_sources:
        raise ValueError(f"Already clipped — this URL exists in the vault.\nURL: {url}")

    logger.info("Fetching transcript…")
    whisper_model = config.get("whisper", {}).get("model", "base")
    transcript_result = get_transcript(url, platform, whisper_model=whisper_model)
    logger.info(
        "Transcript fetched (%d words, method: %s)",
        len(transcript_result.text.split()),
        transcript_result.method,
    )

    today = date.today().isoformat()
    existing_titles = get_existing_titles(vault_path, subfolder=subfolder)
    logger.info("Found %d existing notes in vault", len(existing_titles))

    claude_model = config.get("claude", {}).get("model", "claude-sonnet-4-20250514")
    note = generate_note(
        url, platform, transcript_result.text, today, existing_titles, model=claude_model
    )

    filename = build_filename(note, today)

    if dry_run:
        print(note)
        return

    dest = write_note(note, filename, vault_path=vault_path, subfolder=subfolder)

    if open_after:
        vault_name = Path(vault_path).expanduser().name
        rel = f"{subfolder}/{filename}"
        obsidian_url = (
            f"obsidian://open?vault={urllib.parse.quote(vault_name)}"
            f"&file={urllib.parse.quote(rel)}"
        )
        subprocess.run(["open", obsidian_url], check=False)

    send_notification("Obsidian Clipper", f"Saved: {filename}")
    print(f"\nSaved → {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clip a video into Obsidian.")
    parser.add_argument(
        "url",
        nargs="?",
        help="Video URL to clip. Omit to grab the current Safari tab.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated note to stdout without writing to the vault.",
    )
    parser.add_argument(
        "--no-open",
        action="store_false",
        dest="open_after",
        default=True,
        help="Skip opening the note in Obsidian after saving.",
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = load_config()

    url = args.url
    if not url:
        logger.info("Grabbing URL from Safari…")
        url = get_safari_url()
        logger.info("URL: %s", url)

    try:
        clip(url, config, dry_run=args.dry_run, open_after=args.open_after)
    except (ValueError, RuntimeError) as exc:
        logger.error("%s", exc)
        send_notification("Obsidian Clipper — Error", str(exc)[:100])
        sys.exit(1)


if __name__ == "__main__":
    main()
