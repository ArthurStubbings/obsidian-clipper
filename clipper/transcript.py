"""Fetch or generate a transcript for YouTube videos and Instagram Reels."""

import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from clipper.safari import Platform

logger = logging.getLogger(__name__)

_YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)


@dataclass
class TranscriptResult:
    text: str
    language: str
    method: str  # "youtube_api" | "whisper"


def get_transcript(url: str, platform: Platform, whisper_model: str = "base") -> TranscriptResult:
    if platform == Platform.YOUTUBE:
        return _youtube_transcript(url, whisper_model)
    if platform == Platform.INSTAGRAM_REEL:
        return _whisper_transcript(url, whisper_model)
    raise ValueError(f"Unsupported platform: {platform}")


def _youtube_transcript(url: str, whisper_model: str = "base") -> TranscriptResult:
    m = _YOUTUBE_RE.search(url)
    if not m:
        raise ValueError(f"Could not extract YouTube video ID from: {url}")
    video_id = m.group(1)

    logger.info("Fetching YouTube transcript for video ID: %s", video_id)
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
        text = " ".join(seg.text for seg in fetched)
        return TranscriptResult(text=text, language="en", method="youtube_api")

    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        logger.warning("YouTube transcript API failed (%s) — falling back to Whisper…", exc)
        return _whisper_transcript(url, whisper_model)


def _whisper_transcript(url: str, model_name: str = "base") -> TranscriptResult:
    """Download audio with yt-dlp then transcribe locally with Whisper."""
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "openai-whisper is not installed. Run: pip install openai-whisper"
        )

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = os.path.join(tmp, "audio.%(ext)s")
        logger.info("Downloading audio via yt-dlp…")
        venv_bin = Path(__file__).parent.parent / "venv" / "bin"
        yt_dlp = str(venv_bin / "yt-dlp")
        result = subprocess.run(
            [
                yt_dlp,
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "-o", audio_path,
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")

        downloaded = [f for f in os.listdir(tmp) if f.startswith("audio.")]
        if not downloaded:
            raise RuntimeError("yt-dlp did not produce an audio file.")
        mp3_path = os.path.join(tmp, downloaded[0])

        logger.info("Transcribing audio with Whisper (model: %s)…", model_name)
        model = whisper.load_model(model_name)
        result_w = model.transcribe(mp3_path, language="en")
        text = result_w["text"].strip()
        return TranscriptResult(text=text, language="en", method="whisper")
