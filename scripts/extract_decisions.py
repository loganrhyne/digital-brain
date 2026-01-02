#!/usr/bin/env python3
"""Extract [decision] observations from all notes and build a global decision index."""
from __future__ import annotations

import datetime
import re
from pathlib import Path

FRONTMATTER_BOUNDARY = "---"
KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
DECISION_PATTERN = re.compile(r"^-\s+\[decision\]\s*(?:\{([^}]+)\}\s*)?(.+)$")


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


def extract_decisions_from_note(path: Path) -> list[dict]:
    """Extract all [decision] observations from a note file."""
    decisions = []
    frontmatter = parse_frontmatter(path)
    if not frontmatter:
        return decisions

    note_id = frontmatter.get("id", "")
    note_title = frontmatter.get("title", path.stem.replace("-", " ").title())
    note_type = frontmatter.get("type", "")
    note_tags = frontmatter.get("tags", [])
    note_created = frontmatter.get("created", "")

    # Read file content and look for decision observations
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for line in lines:
        match = DECISION_PATTERN.match(line.strip())
        if match:
            metadata_str = match.group(1)  # Could be None
            decision_text = match.group(2)

            metadata = parse_metadata(metadata_str) if metadata_str else {}

            # Use explicit date from metadata, or fall back to note creation date
            decision_date = metadata.get("date", note_created)

            decisions.append({
                "text": decision_text,
                "date": decision_date,
                "metadata": metadata,
                "source_note": {
                    "id": note_id,
                    "title": note_title,
                    "type": note_type,
                    "tags": note_tags,
                    "path": path,
                }
            })

    return decisions


def collect_all_decisions(repo_root: Path) -> list[dict]:
    """Scan all markdown files and collect decisions."""
    all_decisions = []

    for path in sorted(repo_root.rglob("*.md")):
        # Skip the indices, templates, and _meta directories
        if "indices" in path.parts or "templates" in path.parts or "_meta" in path.parts:
            continue

        decisions = extract_decisions_from_note(path)
        all_decisions.extend(decisions)

    # Sort by date (most recent first), then by source title (alphabetically)
    # This ensures decisions from the same source are adjacent
    all_decisions.sort(
        key=lambda d: (
            -(int(d["date"].replace("-", "")) if d["date"] and d["date"].replace("-", "").isdigit() else 0),
            d["source_note"]["title"]
        )
    )

    return all_decisions


def load_existing_created(index_path: Path) -> str | None:
    """Load creation date from existing index file."""
    if not index_path.exists():
        return None
    frontmatter = parse_frontmatter(index_path)
    if not frontmatter:
        return None
    return frontmatter.get("created")


def build_decision_index(repo_root: Path, index_path: Path) -> None:
    """Build the decision index file."""
    today = datetime.date.today().isoformat()
    created = load_existing_created(index_path) or today

    decisions = collect_all_decisions(repo_root)

    lines: list[str] = [
        FRONTMATTER_BOUNDARY,
        "id: index-decisions",
        "type: index",
        "status: active",
        "tags: [index, decisions]",
        f"created: {created}",
        f"updated: {today}",
        "visibility: private",
        "title: Decision Index",
        FRONTMATTER_BOUNDARY,
        "",
        "# Decision Index",
        "",
        "Global index of all decisions tracked across the digital brain.",
        "",
    ]

    if not decisions:
        lines.append("## Entries")
        lines.append("")
        lines.append("No decisions recorded yet.")
    else:
        # Group by year-month for better organization
        current_period = None

        for decision in decisions:
            decision_date = decision["date"]
            decision_text = decision["text"]
            source = decision["source_note"]

            # Extract year-month for grouping
            if decision_date:
                try:
                    period = decision_date[:7]  # YYYY-MM
                    if period != current_period:
                        current_period = period
                        lines.append(f"## {period}")
                        lines.append("")
                except (IndexError, ValueError):
                    # Invalid date format, skip period header
                    if current_period != "undated":
                        current_period = "undated"
                        lines.append("## Undated")
                        lines.append("")
            else:
                if current_period != "undated":
                    current_period = "undated"
                    lines.append("## Undated")
                    lines.append("")

            # Build the decision entry
            rel_path = source["path"].relative_to(repo_root).as_posix()
            link = Path("..") / rel_path

            # Format: **Date** — **Decision** — From [Note Title](path) — tags
            entry_parts = []

            if decision_date:
                entry_parts.append(f"**{decision_date}**")

            entry_parts.append(decision_text)

            entry_parts.append(f"*From:* [{source['title']}]({link.as_posix()})")

            if source["tags"]:
                tags_str = ", ".join(source["tags"])
                entry_parts.append(f"*Tags:* {tags_str}")

            lines.append("- " + " — ".join(entry_parts))

        lines.append("")

    content = "\n".join(lines) + "\n"
    index_path.write_text(content, encoding="utf-8")


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).resolve().parents[1]
    indices_dir = repo_root / "indices"
    indices_dir.mkdir(exist_ok=True)

    build_decision_index(repo_root, indices_dir / "decisions.md")
    print("Decision index built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
