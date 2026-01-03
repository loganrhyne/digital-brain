#!/usr/bin/env python3
"""Enrich Instapaper articles with AI-generated tags and observations."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import anthropic
except ImportError:
    print("Error: Anthropic package not installed.", file=sys.stderr)
    print("Install with: pip install anthropic", file=sys.stderr)
    sys.exit(1)


FRONTMATTER_BOUNDARY = "---"
KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def parse_frontmatter(content: str) -> tuple[dict, int, int]:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, start_line, end_line) where lines are 0-indexed.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
        return {}, 0, 0

    try:
        end_index = lines[1:].index(FRONTMATTER_BOUNDARY) + 1
    except ValueError:
        return {}, 0, 0

    frontmatter_lines = lines[1:end_index]
    data: dict = {}

    for line in frontmatter_lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        match = KEY_PATTERN.match(line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()

            if value.startswith("[") and value.endswith("]"):
                items = [item.strip().strip('"').strip("'") for item in value[1:-1].split(",") if item.strip()]
                data[key] = items
            elif value == "":
                data[key] = []
            else:
                data[key] = value.strip('"').strip("'")

    return data, 0, end_index + 1


def extract_article_preview(content: str, max_length: int = 2000) -> str:
    """Extract article content preview for AI analysis."""
    # Find the article content section
    match = re.search(r"## Article Content\s*\n\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if match:
        article_text = match.group(1).strip()
        if len(article_text) > max_length:
            return article_text[:max_length] + "..."
        return article_text

    return ""


def generate_enrichment_with_ai(
    title: str,
    url: str,
    article_preview: str,
    existing_highlights: list[str],
    api_key: str,
    model: str = "claude-sonnet-4-5-20250929"
) -> dict:
    """Use Claude to generate tags and observations for an article."""
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are helping enrich a personal knowledge management system. Analyze this article and provide:

1. **Tags** (3-5 relevant topic tags, lowercase, hyphenated)
2. **Observations** in this format:
   - [summary] One sentence summary
   - [key-point] Important insights (2-4 points)
   - [question] Interesting questions raised (1-2 optional)

Article Information:
- Title: {title}
- URL: {url}

Existing Highlights:
{chr(10).join(f"- {h}" for h in existing_highlights) if existing_highlights else "(none)"}

Article Preview:
{article_preview}

Respond in JSON format:
{{
  "tags": ["tag1", "tag2", "tag3"],
  "observations": [
    {{"type": "summary", "text": "..."}},
    {{"type": "key-point", "text": "..."}},
    {{"type": "question", "text": "..."}}
  ]
}}

Focus on practical insights and connections to broader concepts. Be concise and specific."""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        return {"tags": [], "observations": []}

    except Exception as e:
        print(f"Error generating AI enrichment: {e}", file=sys.stderr)
        return {"tags": [], "observations": []}


def extract_existing_highlights(content: str) -> list[str]:
    """Extract existing highlights from observations section."""
    highlights = []

    # Find observations section
    obs_match = re.search(r"## Observations\s*\n(.+?)(?=\n##)", content, re.DOTALL)
    if obs_match:
        obs_section = obs_match.group(1)

        # Extract [key-point] observations (likely from highlights)
        for line in obs_section.splitlines():
            if "[key-point]" in line:
                text = re.sub(r"^-\s*\[key-point\]\s*", "", line.strip())
                if text:
                    highlights.append(text)

    return highlights


def update_frontmatter_tags(content: str, new_tags: list[str]) -> str:
    """Add AI-generated tags to existing frontmatter tags."""
    frontmatter, start, end = parse_frontmatter(content)

    existing_tags = frontmatter.get("tags", [])
    if isinstance(existing_tags, str):
        existing_tags = [existing_tags]

    # Merge tags (avoid duplicates)
    merged_tags = list(set(existing_tags + new_tags))
    merged_tags.sort()

    # Rebuild frontmatter with updated tags
    lines = content.splitlines()
    new_frontmatter = []

    in_frontmatter = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == FRONTMATTER_BOUNDARY:
            in_frontmatter = True
            new_frontmatter.append(line)
            continue

        if in_frontmatter and line.strip() == FRONTMATTER_BOUNDARY:
            in_frontmatter = False
            new_frontmatter.append(line)
            continue

        if in_frontmatter:
            if line.startswith("tags:"):
                # Replace with merged tags
                tags_json = json.dumps(merged_tags)
                new_frontmatter.append(f"tags: {tags_json}")
            else:
                new_frontmatter.append(line)

    # Reconstruct content
    body = "\n".join(lines[end:])
    return "\n".join(new_frontmatter) + "\n" + body


def update_observations(content: str, new_observations: list[dict]) -> str:
    """Add AI-generated observations to observations section."""
    # Find observations section
    obs_match = re.search(r"(## Observations\s*\n)(.+?)((?=\n##)|$)", content, re.DOTALL)

    if not obs_match:
        return content

    section_start = obs_match.group(1)
    existing_obs = obs_match.group(2).strip()

    # Build new observations
    new_obs_lines = []
    for obs in new_observations:
        obs_type = obs.get("type", "key-point")
        obs_text = obs.get("text", "").strip()
        if obs_text:
            new_obs_lines.append(f"- [{obs_type}] {obs_text}")

    # Check if summary placeholder exists
    has_placeholder = "(Add summary after reading)" in existing_obs

    if has_placeholder:
        # Replace placeholder with AI summary
        summary_obs = [o for o in new_observations if o.get("type") == "summary"]
        if summary_obs:
            existing_obs = existing_obs.replace(
                "- [summary] (Add summary after reading)",
                f"- [summary] {summary_obs[0]['text']}"
            )
            # Remove summary from new observations to avoid duplication
            new_observations = [o for o in new_observations if o.get("type") != "summary"]

    # Combine existing and new observations
    combined = existing_obs + "\n" + "\n".join(new_obs_lines)

    # Replace in content
    return content.replace(obs_match.group(0), section_start + combined.strip() + "\n")


def enrich_article(
    file_path: Path,
    api_key: str,
    config: dict,
    dry_run: bool = False
) -> bool:
    """Enrich a single article with AI-generated metadata."""
    content = file_path.read_text(encoding="utf-8")

    # Parse frontmatter
    frontmatter, _, _ = parse_frontmatter(content)

    title = frontmatter.get("title", file_path.stem)
    url = frontmatter.get("source_url", "")

    print(f"Enriching: {title}")

    # Extract article preview
    article_preview = extract_article_preview(content)
    if not article_preview:
        print("  Warning: No article content found, skipping")
        return False

    # Extract existing highlights
    existing_highlights = extract_existing_highlights(content)

    # Generate enrichment
    enrichment = generate_enrichment_with_ai(
        title, url, article_preview, existing_highlights,
        api_key, config.get("model", "claude-sonnet-4-5-20250929")
    )

    if not enrichment.get("tags") and not enrichment.get("observations"):
        print("  Warning: No enrichment generated")
        return False

    # Update content
    updated_content = content

    if enrichment.get("tags") and config.get("generate_tags", True):
        print(f"  Adding tags: {', '.join(enrichment['tags'])}")
        updated_content = update_frontmatter_tags(updated_content, enrichment["tags"])

    if enrichment.get("observations") and config.get("generate_observations", True):
        print(f"  Adding {len(enrichment['observations'])} observations")
        updated_content = update_observations(updated_content, enrichment["observations"])

    # Write updated content
    if dry_run:
        print("  Would update file (dry run)")
        return True

    file_path.write_text(updated_content, encoding="utf-8")
    print("  Enriched successfully")

    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enrich Instapaper articles with AI")
    parser.add_argument("files", nargs="*", help="Specific files to enrich (or all draft articles if not specified)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")

    args = parser.parse_args()

    # Load configuration
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / ".digital-brain" / "instapaper_config.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        return 1

    ai_config = config.get("sync", {}).get("ai_enrichment", {})

    if not ai_config.get("enabled", False):
        print("AI enrichment is disabled in config")
        return 0

    # Get API key
    api_key = args.api_key or ai_config.get("api_key") or None
    if not api_key:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: No API key provided. Use --api-key, set ANTHROPIC_API_KEY env var, or add to config", file=sys.stderr)
        return 1

    # Determine files to enrich
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        # Enrich all draft Instapaper articles
        articles_dir = repo_root / config["output"]["notes_directory"]
        files = sorted(articles_dir.glob("instapaper-*.md"))

    if not files:
        print("No files to enrich")
        return 0

    print(f"Enriching {len(files)} articles...")

    # Enrich each file
    enriched_count = 0
    for file_path in files:
        if enrich_article(file_path, api_key, ai_config, dry_run=args.dry_run):
            enriched_count += 1

    print(f"\nEnriched {enriched_count} articles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
