#!/usr/bin/env python3
"""Shared utilities for extracting observations from notes."""
from __future__ import annotations

import re
from pathlib import Path

FRONTMATTER_BOUNDARY = "---"
KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def parse_frontmatter(path: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
        return None
    try:
        end_index = lines[1:].index(FRONTMATTER_BOUNDARY) + 1
    except ValueError:
        return None
    frontmatter_lines = lines[1:end_index]
    data: dict = {}
    current_key: str | None = None
    for line in frontmatter_lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        match = KEY_PATTERN.match(line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            current_key = key
            if value.startswith("[") and value.endswith("]"):
                items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
                data[key] = items
            elif value == "":
                data[key] = []
            else:
                data[key] = value.strip('"').strip("'")
    return data


def parse_metadata(metadata_str: str) -> dict:
    """Parse metadata string like 'date: 2026-01-15, priority: high' into dict."""
    metadata = {}
    if not metadata_str:
        return metadata

    # Split by comma and parse key:value pairs
    pairs = [p.strip() for p in metadata_str.split(",")]
    for pair in pairs:
        if ":" not in pair:
            continue
        key, value = pair.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata


def extract_observations_from_note(path: Path, observation_tag: str) -> list[dict]:
    """Extract all observations of a specific tag type from a note file.

    Args:
        path: Path to the markdown note file
        observation_tag: Tag to search for (e.g., 'decision', 'event')

    Returns:
        List of observation dictionaries with text, date, metadata, and source info
    """
    observations = []
    frontmatter = parse_frontmatter(path)
    if not frontmatter:
        return observations

    note_id = frontmatter.get("id", "")
    note_title = frontmatter.get("title", path.stem.replace("-", " ").title())
    note_type = frontmatter.get("type", "")
    note_tags = frontmatter.get("tags", [])
    note_created = frontmatter.get("created", "")

    # Create pattern for the specific observation tag
    pattern = re.compile(rf"^-\s+\[{observation_tag}\]\s*(?:\{{([^}}]+)\}}\s*)?(.+)$")

    # Read file content and look for observations
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for line in lines:
        match = pattern.match(line.strip())
        if match:
            metadata_str = match.group(1)  # Could be None
            observation_text = match.group(2)

            metadata = parse_metadata(metadata_str) if metadata_str else {}

            # Use explicit date from metadata, or fall back to note creation date
            observation_date = metadata.get("date", note_created)

            observations.append({
                "text": observation_text,
                "date": observation_date,
                "metadata": metadata,
                "source_note": {
                    "id": note_id,
                    "title": note_title,
                    "type": note_type,
                    "tags": note_tags,
                    "path": path,
                }
            })

    return observations


def collect_all_observations(repo_root: Path, observation_tag: str) -> list[dict]:
    """Scan all markdown files and collect observations of a specific tag type.

    Args:
        repo_root: Root directory of the repository
        observation_tag: Tag to search for (e.g., 'decision', 'event')

    Returns:
        List of all observations, sorted by date (most recent first)
    """
    all_observations = []

    for path in sorted(repo_root.rglob("*.md")):
        # Skip the .digital-brain infrastructure directory
        if ".digital-brain" in path.parts:
            continue

        observations = extract_observations_from_note(path, observation_tag)
        all_observations.extend(observations)

    # Sort by date (most recent first), then by source title (alphabetically)
    # This ensures observations from the same source are adjacent
    all_observations.sort(
        key=lambda d: (
            -(int(d["date"].replace("-", "")) if d["date"] and d["date"].replace("-", "").isdigit() else 0),
            d["source_note"]["title"]
        )
    )

    return all_observations


def load_existing_created(index_path: Path) -> str | None:
    """Load creation date from existing index file."""
    if not index_path.exists():
        return None
    frontmatter = parse_frontmatter(index_path)
    if not frontmatter:
        return None
    return frontmatter.get("created")
