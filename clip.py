#!/usr/bin/env python3
"""clip.py — Obsidian Clipper entrypoint.

Usage:
    python clip.py          # clips the current Safari tab
    python clip.py <url>    # clips an explicit URL (for testing)
"""

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

from clipper.claude import generate_note
from clipper.formatter import build_filename
from clipper.safari import Platform, detect_platform, get_safari_url
from clipper.transcript import get_transcript
from clipper.vault import send_notification, write_note

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as f:
        return yaml.safe_load(f)


def clip(url: str, config: dict) -> None:
    platform = detect_platform(url)
    if platform == Platform.UNSUPPORTED:
        raise ValueError(
            f"Unsupported URL — only YouTube and Instagram Reels are supported.\nURL: {url}"
        )

    logger.info("Platform detected: %s", platform.value)
    logger.info("Fetching transcript…")
    transcript_result = get_transcript(url, platform)
    logger.info(
        "Transcript fetched (%d words, method: %s)",
        len(transcript_result.text.split()),
        transcript_result.method,
    )

    today = date.today().isoformat()
    logger.info("Generating note with Claude…")
    note = generate_note(url, platform, transcript_result.text, today)

    filename = build_filename(note, today)
    dest = write_note(
        note,
        filename,
        vault_path=config["vault"]["path"],
        subfolder=config["vault"].get("subfolder", "Sources"),
    )

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
        clip(url, config)
    except (ValueError, RuntimeError) as exc:
        logger.error("%s", exc)
        send_notification("Obsidian Clipper — Error", str(exc)[:100])
        sys.exit(1)


if __name__ == "__main__":
    main()
