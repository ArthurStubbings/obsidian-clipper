"""Grab the current Safari URL and detect the video platform."""

import re
import subprocess
from enum import Enum


class Platform(Enum):
    YOUTUBE = "YouTube"
    INSTAGRAM_REEL = "Instagram Reel"
    UNSUPPORTED = "Unsupported"


_YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
_INSTAGRAM_REEL_RE = re.compile(r"instagram\.com/(?:reel|reels)/([A-Za-z0-9_-]+)")

_APPLESCRIPT = """\
tell application "Safari"
    if (count of windows) is 0 then error "Safari has no open windows"
    set currentTab to current tab of front window
    return URL of currentTab
end tell
"""


def get_safari_url() -> str:
    """Return the URL of the active Safari tab."""
    result = subprocess.run(
        ["osascript", "-e", _APPLESCRIPT],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"AppleScript failed: {result.stderr.strip()}")
    url = result.stdout.strip()
    if not url:
        raise RuntimeError("Safari returned an empty URL")
    return url


def detect_platform(url: str) -> Platform:
    if _YOUTUBE_RE.search(url):
        return Platform.YOUTUBE
    if _INSTAGRAM_REEL_RE.search(url):
        return Platform.INSTAGRAM_REEL
    return Platform.UNSUPPORTED


def extract_video_id(url: str, platform: Platform) -> str | None:
    if platform == Platform.YOUTUBE:
        m = _YOUTUBE_RE.search(url)
        return m.group(1) if m else None
    if platform == Platform.INSTAGRAM_REEL:
        m = _INSTAGRAM_REEL_RE.search(url)
        return m.group(1) if m else None
    return None
