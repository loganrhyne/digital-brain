#!/usr/bin/env python3
"""Import articles from Instapaper into the digital brain."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode

try:
    import requests
    from requests_oauthlib import OAuth1
except ImportError:
    print("Error: Required packages not installed.", file=sys.stderr)
    print("Install with: pip install requests requests-oauthlib", file=sys.stderr)
    sys.exit(1)


# Instapaper API endpoints
API_BASE = "https://www.instapaper.com/api/1"
BOOKMARKS_LIST = f"{API_BASE}/bookmarks/list"
BOOKMARKS_TEXT = f"{API_BASE}/bookmarks/get_text"
HIGHLIGHTS_LIST = f"{API_BASE.replace('/1', '/1.1')}/bookmarks"


def load_config(config_path: Path) -> dict:
    """Load configuration from JSON file."""
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        print("Copy .digital-brain/instapaper_config.example.json to .digital-brain/instapaper_config.json", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_sync_state(state_path: Path) -> dict:
    """Load sync state tracking which articles have been imported."""
    if not state_path.exists():
        return {
            "last_sync": None,
            "imported_bookmark_ids": [],
            "last_bookmark_id": None
        }

    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sync_state(state_path: Path, state: dict) -> None:
    """Save sync state to track imported articles."""
    state["last_sync"] = datetime.datetime.now().isoformat()
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def create_oauth_session(config: dict) -> OAuth1:
    """Create OAuth1 session for Instapaper API."""
    oauth = config["oauth"]
    return OAuth1(
        oauth["consumer_key"],
        oauth["consumer_secret"],
        oauth["access_token"],
        oauth["access_token_secret"]
    )


def fetch_bookmarks(auth: OAuth1, folder: str = "archive", limit: int = 500) -> list[dict]:
    """Fetch bookmarks from Instapaper."""
    params = {
        "folder": folder,
        "limit": limit
    }

    response = requests.post(BOOKMARKS_LIST, auth=auth, data=params)
    response.raise_for_status()

    bookmarks = response.json()

    # API returns array where first element is user info, rest are bookmarks
    if isinstance(bookmarks, list) and len(bookmarks) > 1:
        return bookmarks[1:]  # Skip user object

    return []


def fetch_article_text(auth: OAuth1, bookmark_id: int) -> Optional[str]:
    """Fetch full article text for a bookmark."""
    params = {"bookmark_id": bookmark_id}

    try:
        response = requests.post(BOOKMARKS_TEXT, auth=auth, data=params)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Warning: Could not fetch text for bookmark {bookmark_id}: {e}", file=sys.stderr)
        return None


def fetch_highlights(auth: OAuth1, bookmark_id: int) -> list[dict]:
    """Fetch highlights for a bookmark."""
    url = f"{HIGHLIGHTS_LIST}/{bookmark_id}/highlights"

    try:
        response = requests.post(url, auth=auth)
        response.raise_for_status()
        highlights = response.json()

        # Filter out non-highlight objects
        if isinstance(highlights, list):
            return [h for h in highlights if isinstance(h, dict) and h.get("type") == "highlight"]

        return []
    except Exception as e:
        print(f"Warning: Could not fetch highlights for bookmark {bookmark_id}: {e}", file=sys.stderr)
        return []


def generate_note_id(bookmark_id: int, title: str, prefix: str = "instapaper") -> str:
    """Generate a unique note ID for an article."""
    # Use bookmark ID as primary identifier with slug from title
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:30].strip("-")
    return f"{prefix}-{bookmark_id}-{slug}"


def generate_filename(note_id: str) -> str:
    """Generate filename from note ID."""
    return f"{note_id}.md"


def extract_domain(url: str) -> str:
    """Extract domain from URL for creator field."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except Exception:
        return "Unknown"


def clean_html(text: str) -> str:
    """Basic HTML cleaning for article text."""
    # Remove common HTML tags (basic cleanup)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")

    # Clean up whitespace
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()


def format_highlights_as_observations(highlights: list[dict]) -> str:
    """Convert Instapaper highlights to observation format."""
    if not highlights:
        return "- [summary] (Add summary after reading)"

    observations = []
    for highlight in highlights:
        text = highlight.get("text", "").strip()
        if text:
            # Use [key-point] for highlights by default
            observations.append(f"- [key-point] {text}")

    # Always add a summary placeholder
    observations.insert(0, "- [summary] (Add summary after reading)")

    return "\n".join(observations)


def create_article_note(
    bookmark: dict,
    article_text: Optional[str],
    highlights: list[dict],
    config: dict
) -> tuple[str, str]:
    """Create a media note from Instapaper bookmark data."""
    bookmark_id = bookmark.get("bookmark_id")
    title = bookmark.get("title", "Untitled Article")
    url = bookmark.get("url", "")
    description = bookmark.get("description", "")
    time = bookmark.get("time", 0)  # Unix timestamp
    progress = bookmark.get("progress", 0.0)
    folder = bookmark.get("folder_name", "Archive")

    # Generate note metadata
    note_id = generate_note_id(bookmark_id, title, config["output"]["id_prefix"])
    filename = generate_filename(note_id)

    # Convert timestamp to ISO date
    if time:
        created_date = datetime.datetime.fromtimestamp(time).date().isoformat()
    else:
        created_date = datetime.date.today().isoformat()

    today = datetime.date.today().isoformat()

    # Extract creator from URL
    creator = extract_domain(url)

    # Format observations from highlights
    observations = format_highlights_as_observations(highlights)

    # Format article content
    if article_text:
        content = clean_html(article_text)
    else:
        content = f"[Article text not available. Read at source: {url}]"
        if description:
            content += f"\n\n**Description**: {description}"

    # Format tags
    tags = ["article", "instapaper"]
    if folder and folder.lower() != "archive":
        tags.append(folder.lower().replace(" ", "-"))
    tags_str = json.dumps(tags)

    # Build note content from template
    note_content = f"""---
id: "{note_id}"
type: media
status: {config["output"]["default_status"]}
tags: {tags_str}
created: "{created_date}"
updated: "{today}"
visibility: {config["output"]["default_visibility"]}
title: "{title}"
media_type: "article"
source_url: "{url}"
creator: "{creator}"
published: "{created_date}"
instapaper_id: {bookmark_id}
instapaper_folder: "{folder}"
instapaper_archived: "{created_date}"
reading_progress: {int(progress * 100)}
---

# {title}

## Observations
{observations}

## Metadata
- **Type**: article
- **Source**: [{url}]({url})
- **Creator**: {creator}
- **Published**: {created_date}
- **Archived**: {created_date}
- **Instapaper ID**: {bookmark_id}
- **Folder**: {folder}
- **Reading Progress**: {int(progress * 100)}%

## Article Content

{content}

## Notes

(Add personal reflections, connections, and analysis here)

## Relations
"""

    return filename, note_content


def import_bookmark(
    bookmark: dict,
    auth: OAuth1,
    config: dict,
    output_dir: Path,
    dry_run: bool = False
) -> Optional[str]:
    """Import a single bookmark as a media note."""
    bookmark_id = bookmark.get("bookmark_id")
    title = bookmark.get("title", "Untitled")

    print(f"Processing: {title} (ID: {bookmark_id})")

    # Fetch article text if enabled
    article_text = None
    if config["sync"].get("include_article_text", True):
        article_text = fetch_article_text(auth, bookmark_id)

    # Fetch highlights if enabled
    highlights = []
    if config["sync"].get("include_highlights", True):
        highlights = fetch_highlights(auth, bookmark_id)
        print(f"  Found {len(highlights)} highlights")

    # Generate note
    filename, note_content = create_article_note(bookmark, article_text, highlights, config)

    # Write note to file
    output_path = output_dir / filename

    if output_path.exists():
        print(f"  Skipping (already exists): {output_path}")
        return None

    if dry_run:
        print(f"  Would create: {output_path}")
        return str(bookmark_id)

    output_path.write_text(note_content, encoding="utf-8")
    print(f"  Created: {output_path}")

    return str(bookmark_id)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import Instapaper articles to digital brain")
    parser.add_argument("--limit", type=int, help="Maximum number of articles to import")
    parser.add_argument("--folder", default="archive", help="Instapaper folder to import (default: archive)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without creating files")
    parser.add_argument("--full-archive", action="store_true", help="Import entire archive (ignores limit)")

    args = parser.parse_args()

    # Determine paths
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / ".digital-brain" / "instapaper_config.json"
    state_path = repo_root / ".digital-brain" / "instapaper_sync_state.json"

    # Load configuration
    config = load_config(config_path)
    sync_state = load_sync_state(state_path)

    # Determine output directory
    output_dir = repo_root / config["output"]["notes_directory"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create OAuth session
    auth = create_oauth_session(config)

    # Determine import limit
    if args.full_archive:
        limit = 500  # API max per request
    else:
        limit = args.limit or config["sync"].get("max_articles_per_run", 50)

    print(f"Fetching up to {limit} bookmarks from '{args.folder}' folder...")

    # Fetch bookmarks
    try:
        bookmarks = fetch_bookmarks(auth, folder=args.folder, limit=limit)
    except Exception as e:
        print(f"Error fetching bookmarks: {e}", file=sys.stderr)
        return 1

    print(f"Found {len(bookmarks)} bookmarks")

    if not bookmarks:
        print("No bookmarks to import")
        return 0

    # Import each bookmark
    imported_ids = []
    for bookmark in bookmarks:
        bookmark_id = str(bookmark.get("bookmark_id"))

        # Skip if already imported
        if bookmark_id in sync_state["imported_bookmark_ids"]:
            print(f"Skipping already imported: {bookmark.get('title')} (ID: {bookmark_id})")
            continue

        # Import the bookmark
        result_id = import_bookmark(bookmark, auth, config, output_dir, dry_run=args.dry_run)
        if result_id:
            imported_ids.append(result_id)

    # Update sync state
    if imported_ids and not args.dry_run:
        sync_state["imported_bookmark_ids"].extend(imported_ids)
        save_sync_state(state_path, sync_state)
        print(f"\nImported {len(imported_ids)} new articles")
    elif args.dry_run:
        print(f"\nWould import {len(imported_ids)} new articles")
    else:
        print("\nNo new articles to import")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
