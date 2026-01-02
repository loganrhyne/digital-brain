#!/usr/bin/env python3
from __future__ import annotations

import datetime
import os
import re
from pathlib import Path

FRONTMATTER_BOUNDARY = "---"
KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def parse_frontmatter(path: Path) -> dict | None:
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
                data[key] = value.strip("\"").strip("'")
            continue
        if line.lstrip().startswith("- ") and current_key:
            item = line.lstrip()[2:].strip()
            existing = data.get(current_key)
            if not isinstance(existing, list):
                existing = []
            existing.append(item)
            data[current_key] = existing
    return data


def collect_notes(repo_root: Path, note_type: str) -> list[dict]:
    notes: list[dict] = []
    for path in sorted(repo_root.rglob("*.md")):
        frontmatter = parse_frontmatter(path)
        if not frontmatter:
            continue
        if frontmatter.get("type") != note_type:
            continue
        rel_path = path.relative_to(repo_root).as_posix()
        title = frontmatter.get("title") or path.stem.replace("-", " ").title()
        notes.append(
            {
                "id": frontmatter.get("id", ""),
                "title": title,
                "path": rel_path,
                "status": frontmatter.get("status", ""),
            }
        )
    notes.sort(key=lambda item: (item["title"].lower(), item["id"]))
    return notes


def load_existing_created(index_path: Path) -> str | None:
    if not index_path.exists():
        return None
    frontmatter = parse_frontmatter(index_path)
    if not frontmatter:
        return None
    return frontmatter.get("created")


def build_index(repo_root: Path, note_type: str, index_path: Path) -> None:
    today = datetime.date.today().isoformat()
    created = load_existing_created(index_path) or today
    if note_type == "concept":
        title = "Concepts Index"
        index_id = "index-concepts"
        tags = "[index, concepts]"
    elif note_type == "book":
        title = "Books Index"
        index_id = "index-books"
        tags = "[index, books]"
    elif note_type == "recipe":
        title = "Recipes Index"
        index_id = "index-recipes"
        tags = "[index, recipes]"
    elif note_type == "poetry":
        title = "Poetry Index"
        index_id = "index-poetry"
        tags = "[index, poetry]"
    else:
        raise ValueError(f"Unsupported note type: {note_type}")

    notes = collect_notes(repo_root, note_type)

    lines: list[str] = [
        FRONTMATTER_BOUNDARY,
        f"id: {index_id}",
        "type: index",
        "status: active",
        f"tags: {tags}",
        f"created: {created}",
        f"updated: {today}",
        "visibility: private",
        f"title: {title}",
        FRONTMATTER_BOUNDARY,
        "",
        f"# {title}",
        "",
        "## Entries",
    ]

    if not notes:
        lines.append("No entries yet.")
    else:
        for note in notes:
            link = Path("..") / note["path"]
            label = note["title"]
            entry = f"- [{label}]({link.as_posix()}) — {note['id']}"
            if note["status"]:
                entry += f" — {note['status']}"
            lines.append(entry)

    content = "\n".join(lines) + "\n"
    index_path.write_text(content, encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    indices_dir = repo_root / "indices"
    indices_dir.mkdir(exist_ok=True)

    build_index(repo_root, "concept", indices_dir / "concepts.md")
    build_index(repo_root, "book", indices_dir / "books.md")
    build_index(repo_root, "recipe", indices_dir / "recipes.md")
    build_index(repo_root, "poetry", indices_dir / "poetry.md")
    print("Indices rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
