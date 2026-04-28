"""Extract metadata from a generated note and build the output filename."""

import re
import unicodedata


_TITLE_RE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)


def extract_title(note: str) -> str:
    """Pull the title value out of the YAML frontmatter."""
    m = _TITLE_RE.search(note)
    if not m:
        return "untitled"
    return m.group(1).strip().strip('"').strip("'")


def slugify(text: str) -> str:
    """Convert a title to a filesystem-safe slug."""
    # Normalise unicode to ASCII
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    # Truncate to avoid overly long filenames
    return text[:80]


def build_filename(note: str, date: str) -> str:
    """Return the filename for the note, e.g. 2026-04-28-my-video-title.md"""
    title = extract_title(note)
    slug = slugify(title)
    return f"{date}-{slug}.md"
