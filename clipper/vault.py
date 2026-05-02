"""Write the generated note to the Obsidian vault."""

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def resolve_vault_path(raw_path: str) -> Path:
    """Expand ~ and env vars and return an absolute Path."""
    return Path(os.path.expandvars(os.path.expanduser(raw_path))).resolve()


def write_note(note: str, filename: str, vault_path: str, subfolder: str = "Sources") -> Path:
    """Write *note* to <vault>/<subfolder>/<filename>, creating dirs as needed."""
    vault = resolve_vault_path(vault_path)
    dest_dir = vault / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / filename
    dest.write_text(note, encoding="utf-8")
    logger.info("Note written to: %s", dest)
    return dest


def get_existing_titles(vault_path: str, subfolder: str = "Sources") -> list[str]:
    """Return the title frontmatter value from every .md file in the vault subfolder."""
    import glob
    import re
    vault = resolve_vault_path(vault_path)
    title_re = re.compile(r"^title:\s*(.+)$", re.MULTILINE)
    titles = []
    search_dir = vault / subfolder
    for path in glob.glob(str(search_dir / "*.md")):
        try:
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            m = title_re.search(text)
            if m:
                titles.append(m.group(1).strip().strip('"').strip("'"))
        except OSError:
            continue
    return sorted(titles)


def send_notification(title: str, message: str) -> None:
    """Show a macOS notification using osascript."""
    script = (
        f'display notification "{message}" with title "{title}"'
    )
    try:
        subprocess.run(["osascript", "-e", script], timeout=5, check=True)
    except Exception as exc:
        logger.warning("Could not send macOS notification: %s", exc)
