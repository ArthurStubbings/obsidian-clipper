"""Call the Anthropic API to generate a structured Obsidian note."""

import logging
import os

import anthropic

from clipper.safari import Platform

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-20250514"

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

_CLASSIFY_PROMPT = """\
Classify this video transcript into exactly one of three types:

- reference: a structured list of N items, concepts, tips, steps, mistakes, rules, or tools
- tutorial: a how-to walkthrough focused on building or doing one specific thing
- essay: a talk, interview, or explanation built around a central argument or narrative

Respond with a single word: reference, tutorial, or essay.

TRANSCRIPT (first 1500 chars):
{transcript}
"""

# --- Prompt templates per video type ---

_ESSAY_PROMPT = """\
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

_TUTORIAL_PROMPT = """\
Convert the following tutorial transcript into an Obsidian markdown note.

Important: tutorials often use a demo project as a vehicle. Your job is to capture the \
SKILL or TOOL being taught — not the demo. If someone built a game to teach Claude Code, \
the note is about Claude Code, not the game.

URL: {url}
Platform: {platform}

TRANSCRIPT:
{transcript}

Output the note using EXACTLY this structure:

---
title: <descriptive title — the skill or tool being taught, not the demo project>
source: {url}
platform: {platform}
creator: <channel name or author if detectable, otherwise "Unknown">
date_saved: {date}
duration: <estimated duration in minutes based on transcript length, format: "X min">
tags: [tag1, tag2, tag3, tag4]
status: inbox
---

## What you learn
<1–2 sentences on the skill or capability this tutorial gives you>

## Steps
1. <concise step — focus on the transferable process, not demo-specific details>
2. <concise step>
3. <concise step>
(continue for all major steps — be specific, include commands or values where mentioned)

## Key gotchas
- <non-obvious thing that could trip you up>
- <non-obvious thing that could trip you up (if any)>

## Actions
- [ ] <specific next step to apply this skill>
- [ ] <specific next step to apply this skill>
- [ ] <specific next step to apply this skill (if warranted)>

## Related notes
- [[<suggested Obsidian note title>]]
- [[<suggested Obsidian note title>]]

## Source
[View original]({url})
"""

_REFERENCE_PROMPT = """\
Convert the following reference/list video transcript into an Obsidian markdown note.

URL: {url}
Platform: {platform}

TRANSCRIPT:
{transcript}

Output the note using EXACTLY this structure:

---
title: <descriptive title — what the list is>
source: {url}
platform: {platform}
creator: <channel name or author if detectable, otherwise "Unknown">
date_saved: {date}
duration: <estimated duration in minutes based on transcript length, format: "X min">
tags: [tag1, tag2, tag3, tag4]
status: inbox
---

## Overview
<1–2 sentences on what this list covers and why it matters>

## Items
List EVERY item covered in the video. For each one:

### <Item name or number — title>
<1–2 sentences explaining what it is and why it matters>

## Top picks
- **<item>** — <one sentence on why this one stands out>
- **<item>** — <one sentence on why this one stands out>
- **<item>** — <one sentence on why this one stands out>

## Actions
- [ ] <specific next step based on the most relevant item>
- [ ] <specific next step based on the most relevant item>
- [ ] <specific next step based on the most relevant item (if warranted)>

## Related notes
- [[<suggested Obsidian note title>]]
- [[<suggested Obsidian note title>]]

## Source
[View original]({url})
"""

_PROMPTS = {
    "essay": _ESSAY_PROMPT,
    "tutorial": _TUTORIAL_PROMPT,
    "reference": _REFERENCE_PROMPT,
}


def _classify(client: anthropic.Anthropic, transcript: str, model: str) -> str:
    """Return 'reference', 'tutorial', or 'essay'."""
    response = client.messages.create(
        model=model,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": _CLASSIFY_PROMPT.format(transcript=transcript[:1500]),
        }],
    )
    label = response.content[0].text.strip().lower()
    if label not in _PROMPTS:
        logger.warning("Unexpected classification '%s', falling back to essay", label)
        return "essay"
    return label


def generate_note(
    url: str,
    platform: Platform,
    transcript: str,
    date: str,
    existing_titles: list[str] | None = None,
    model: str = _DEFAULT_MODEL,
) -> str:
    """Classify the transcript, then generate a format-appropriate Obsidian note."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment.")

    client = anthropic.Anthropic(api_key=api_key)

    logger.info("Classifying video type…")
    video_type = _classify(client, transcript, model)
    logger.info("Video type: %s", video_type)

    prompt = _PROMPTS[video_type].format(
        url=url,
        platform=platform.value,
        transcript=transcript,
        date=date,
    )

    # Build user content: existing titles block is cached (semi-static across a session),
    # followed by the variable prompt. System prompt is also marked for caching.
    user_content: list[dict] = []
    if existing_titles:
        titles_list = "\n".join(f"- {t}" for t in existing_titles)
        user_content.append({
            "type": "text",
            "text": (
                "EXISTING VAULT NOTES (only suggest [[wikilinks]] to notes from this list):\n"
                + titles_list
            ),
            "cache_control": {"type": "ephemeral"},
        })
    user_content.append({"type": "text", "text": prompt})

    logger.info("Generating note with Claude (%s)…", model)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[{
            "type": "text",
            "text": _SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_content}],
    )

    note = message.content[0].text.strip()
    logger.debug("Claude response:\n%s", note)

    usage = message.usage
    logger.info(
        "Tokens — input: %d (cache_read: %d, cache_write: %d), output: %d",
        usage.input_tokens,
        getattr(usage, "cache_read_input_tokens", 0),
        getattr(usage, "cache_creation_input_tokens", 0),
        usage.output_tokens,
    )

    return note
