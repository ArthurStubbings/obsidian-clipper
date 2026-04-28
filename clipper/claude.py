"""Call the Anthropic API to generate a structured Obsidian note."""

import logging
import os

import anthropic

from clipper.safari import Platform

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"

_SYSTEM_PROMPT = """\
You are an expert knowledge distiller. Your job is to convert video transcripts into \
concise, high-signal Obsidian markdown notes for a personal knowledge management system.

Rules:
- Be specific and concrete — avoid vague generalisations
- Action items must be genuinely actionable, not restatements of summary points
- Tags should be 2–4 lowercase words separated by hyphens, reflecting themes not topics
- Related note titles should be plausible Obsidian note names the user might already have
- Output ONLY the raw markdown — no preamble, no explanation, no code fences
"""

_USER_PROMPT = """\
Convert the following video transcript into an Obsidian markdown note.

URL: {url}
Platform: {platform}

TRANSCRIPT:
{transcript}

Output the note using EXACTLY this structure:

---
title: <descriptive title derived from the content, not the video title>
source: {url}
platform: {platform}
creator: <channel name or author if detectable, otherwise "Unknown">
date_saved: {date}
duration: <estimated duration in minutes based on transcript length, format: "X min">
tags: [tag1, tag2, tag3, tag4]
status: inbox
---

## Summary
- <key insight — one sentence>
- <key insight — one sentence>
- <key insight — one sentence>
- <key insight — one sentence (if warranted)>
- <key insight — one sentence (if warranted)>

## Key idea
<2–3 sentences capturing the single most important concept in the video>

## Actions
- [ ] <specific, doable next step>
- [ ] <specific, doable next step>
- [ ] <specific, doable next step>
- [ ] <specific, doable next step (if warranted)>
- [ ] <specific, doable next step (if warranted)>

## Related notes
- [[<suggested Obsidian note title>]]
- [[<suggested Obsidian note title>]]
- [[<suggested Obsidian note title (if warranted)>]]

## Source
[View original]({url})
"""


def generate_note(url: str, platform: Platform, transcript: str, date: str) -> str:
    """Send transcript to Claude and return the formatted markdown note."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment.")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = _USER_PROMPT.format(
        url=url,
        platform=platform.value,
        transcript=transcript,
        date=date,
    )

    logger.info("Sending transcript to Claude (%s)…", MODEL)
    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    note = message.content[0].text.strip()
    logger.debug("Claude response:\n%s", note)
    return note
