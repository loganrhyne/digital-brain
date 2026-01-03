#!/usr/bin/env python3
"""Extract all dated observations from all notes and build a global timeline index."""
from __future__ import annotations

import datetime
from pathlib import Path

from observation_utils import (
    FRONTMATTER_BOUNDARY,
    collect_all_dated_observations,
    load_existing_created,
)


def build_timeline_index(repo_root: Path, index_path: Path) -> None:
    """Build the timeline index file."""
    today = datetime.date.today().isoformat()
    created = load_existing_created(index_path) or today

    observations = collect_all_dated_observations(repo_root)

    lines: list[str] = [
        FRONTMATTER_BOUNDARY,
        "id: index-timeline",
        "type: index",
        "status: active",
        "tags: [index, timeline, events]",
        f"created: {created}",
        f"updated: {today}",
        "visibility: private",
        "title: Timeline Index",
        FRONTMATTER_BOUNDARY,
        "",
        "# Timeline Index",
        "",
        "Chronological index of all dated observations tracked across the digital brain.",
        "",
    ]

    if not observations:
        lines.append("## Entries")
        lines.append("")
        lines.append("No dated observations recorded yet.")
    else:
        # Group by year-month for better organization
        current_period = None

        for obs in observations:
            obs_date = obs["date"]
            obs_text = obs["text"]
            obs_tag = obs["tag"]
            source = obs["source_note"]

            # Extract year-month for grouping
            if obs_date:
                try:
                    period = obs_date[:7]  # YYYY-MM
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

            # Build the observation entry
            rel_path = source["path"].relative_to(repo_root).as_posix()
            link = Path("..") / rel_path

            # Format: **Date** — [tag] — **Observation** — From [Note Title](path) — tags
            entry_parts = []

            if obs_date:
                entry_parts.append(f"**{obs_date}**")

            # Include the observation tag type
            entry_parts.append(f"`[{obs_tag}]`")

            entry_parts.append(obs_text)

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
    repo_root = Path(__file__).resolve().parents[2]
    indices_dir = repo_root / ".digital-brain" / "indices"
    indices_dir.mkdir(exist_ok=True)

    build_timeline_index(repo_root, indices_dir / "timeline.md")
    print("Timeline index built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
