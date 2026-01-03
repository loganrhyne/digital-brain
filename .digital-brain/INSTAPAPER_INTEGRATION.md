# Instapaper Integration Guide

This guide explains how to integrate your Instapaper archive with the digital brain, enabling automatic import of articles with highlights.

## Overview

The Instapaper integration provides:
- **One-time bulk import** of archived articles
- **Continuous sync** via cron for newly archived articles
- **Highlight extraction** as observations
- **AI enrichment** (optional) for tags and observations
- **Deduplication** to avoid re-importing articles

## Setup

### 1. Install Python Dependencies

```bash
pip install requests requests-oauthlib
```

For AI enrichment (optional):
```bash
pip install anthropic
```

### 2. Configure OAuth Credentials

1. Copy the example config:
   ```bash
   cd .digital-brain
   cp instapaper_config.example.json instapaper_config.json
   ```

2. Get your Instapaper OAuth credentials:
   - Visit: https://www.instapaper.com/main/request_oauth_consumer_token
   - Copy your consumer key and secret
   - Use the Instapaper API or a library to obtain access token and secret

3. Edit `instapaper_config.json`:
   ```json
   {
     "oauth": {
       "consumer_key": "your-consumer-key",
       "consumer_secret": "your-consumer-secret",
       "access_token": "your-access-token",
       "access_token_secret": "your-access-token-secret"
     }
   }
   ```

### 3. Test the Connection

Run a dry-run import to verify credentials:

```bash
.digital-brain/scripts/instapaper_import.py --dry-run --limit 5
```

If successful, you should see a list of articles that would be imported.

## Usage

### One-Time Archive Import

Import your entire archive (recommended to start with a smaller batch):

```bash
# Import first 50 archived articles
.digital-brain/scripts/instapaper_import.py --limit 50

# Import full archive (may take a while)
.digital-brain/scripts/instapaper_import.py --full-archive
```

### Continuous Sync with Cron

Set up automatic daily sync:

1. Make the sync script executable (already done):
   ```bash
   chmod +x .digital-brain/scripts/instapaper_sync.sh
   ```

2. Add to crontab:
   ```bash
   crontab -e
   ```

3. Add this line (runs daily at 2 AM):
   ```cron
   0 2 * * * /home/user/digital-brain/.digital-brain/scripts/instapaper_sync.sh >> /tmp/instapaper-sync.log 2>&1
   ```

### Manual Sync

Run sync manually:

```bash
# Basic sync
.digital-brain/scripts/instapaper_sync.sh

# Sync with AI enrichment
.digital-brain/scripts/instapaper_sync.sh --enrich

# Dry run to see what would be imported
.digital-brain/scripts/instapaper_sync.sh --dry-run
```

## Configuration Options

Edit `.digital-brain/instapaper_config.json` to customize behavior:

### Sync Settings

```json
{
  "sync": {
    "import_archived_only": true,        // Only import archived articles
    "include_highlights": true,           // Fetch highlights from API
    "max_articles_per_run": 50,          // Limit per sync run
    "ai_enrichment": {
      "enabled": false,                   // Enable AI enrichment
      "generate_tags": true,              // Generate tags based on content
      "generate_observations": true,      // Generate observations
      "model": "claude-sonnet-4-5-20250929"
    }
  }
}
```

### Output Settings

```json
{
  "output": {
    "notes_directory": "media/articles",  // Where to save notes
    "id_prefix": "instapaper",            // Note ID prefix
    "default_status": "draft",            // Initial status (draft/active)
    "default_visibility": "private"       // Visibility setting
  }
}
```

## AI Enrichment

AI enrichment uses Claude to analyze articles and generate:
- **Tags**: Topic tags based on content (e.g., "ai", "productivity", "philosophy")
- **Observations**: Summary and key points

### Enable AI Enrichment

1. Get an Anthropic API key from https://console.anthropic.com/

2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   ```

3. Enable in config:
   ```json
   {
     "sync": {
       "ai_enrichment": {
         "enabled": true,
         "generate_tags": true,
         "generate_observations": true
       }
     }
   }
   ```

4. Run enrichment on existing articles:
   ```bash
   .digital-brain/scripts/instapaper_enrich.py
   ```

   Or enrich specific files:
   ```bash
   .digital-brain/scripts/instapaper_enrich.py media/articles/instapaper-*.md
   ```

## Article Note Structure

Imported articles follow this structure:

```markdown
---
id: "instapaper-{bookmark_id}-{title-slug}"
type: media
status: draft
tags: ["article", "instapaper", ...]
created: "2026-01-03"
updated: "2026-01-03"
visibility: private
title: "Article Title"
media_type: "article"
source_url: "https://example.com/article"
creator: "example.com"
published: "2026-01-03"
instapaper_id: 123456
instapaper_folder: "Archive"
instapaper_archived: "2026-01-03"
reading_progress: 100
---

# Article Title

## Observations
- [summary] (Add summary after reading)
- [key-point] Highlighted passage 1
- [key-point] Highlighted passage 2

## Metadata
- **Type**: article
- **Source**: [https://example.com/article](https://example.com/article)
- **Creator**: example.com
- **Published**: 2026-01-03
- **Archived**: 2026-01-03
- **Instapaper ID**: 123456
- **Folder**: Archive
- **Reading Progress**: 100%

## Article Content

[Full article text...]

## Notes

(Add personal reflections, connections, and analysis here)

## Relations
```

## Workflow Recommendations

### Initial Setup (Week 1)

1. Import recent articles (last 50-100):
   ```bash
   .digital-brain/scripts/instapaper_import.py --limit 100
   ```

2. Review imported notes, add observations and relationships

3. Test AI enrichment on a few articles:
   ```bash
   .digital-brain/scripts/instapaper_enrich.py media/articles/instapaper-*.md --dry-run
   ```

4. Commit imported articles:
   ```bash
   git add media/articles/
   git commit -m "Import initial Instapaper articles"
   ```

### Ongoing Sync (After Setup)

1. Set up daily cron job for automatic sync

2. Weekly review session:
   - Check for new draft articles in `media/articles/`
   - Add observations, notes, and relationships
   - Change status from `draft` to `active`
   - Commit reviewed articles

3. Periodically run enrichment on draft articles:
   ```bash
   .digital-brain/scripts/instapaper_enrich.py
   ```

### Archive Exploration (As Needed)

When researching a topic, import older related articles:

1. Search your Instapaper archive (web interface)

2. Import specific time periods or folders:
   ```bash
   .digital-brain/scripts/instapaper_import.py --limit 100 --folder "Research"
   ```

## Troubleshooting

### "No bookmarks to import"

- Check that you have archived articles in Instapaper
- Verify OAuth credentials are correct
- Try with `--folder unread` to import unread articles

### "Required packages not installed"

Install dependencies:
```bash
pip install requests requests-oauthlib
```

### Highlights not appearing

- Highlights require Instapaper Premium subscription
- Check API response by running with increased verbosity
- Verify `include_highlights: true` in config

### Duplicate articles

The sync state tracks imported bookmark IDs in `.digital-brain/instapaper_sync_state.json`. To re-import an article:

1. Delete the note file
2. Remove bookmark ID from sync state file
3. Run import again

### AI enrichment fails

- Verify Anthropic API key is set: `echo $ANTHROPIC_API_KEY`
- Check that `anthropic` package is installed: `pip install anthropic`
- Review error messages in output

## Advanced Usage

### Custom Import Filters

Modify `instapaper_import.py` to filter by:
- Date range (time field)
- Folder name
- Reading progress
- Article length

### Batch Processing

Process large archives in batches:

```bash
for i in {1..10}; do
    .digital-brain/scripts/instapaper_import.py --limit 100
    sleep 5  # Rate limiting
done
```

### Integration with MCP

If using the Instapaper-MCP server:
- MCP provides interactive workflows (weekly digests, research synthesis)
- Scripts provide automated batch processing
- Use MCP for ad-hoc queries, scripts for routine sync

## File Locations

```
.digital-brain/
├── instapaper_config.json          # OAuth credentials & settings (git-ignored)
├── instapaper_config.example.json  # Config template
├── instapaper_sync_state.json      # Sync state tracking (git-ignored)
├── scripts/
│   ├── instapaper_import.py        # Core import script
│   ├── instapaper_enrich.py        # AI enrichment script
│   └── instapaper_sync.sh          # Cron-compatible sync wrapper
└── templates/
    └── instapaper-article.md       # Article note template

media/articles/
└── instapaper-*.md                 # Imported article notes
```

## Next Steps

1. Complete OAuth setup and test connection
2. Import a small batch (50-100 articles) to validate workflow
3. Set up cron for daily sync
4. Consider enabling AI enrichment for automatic tagging
5. Establish a weekly review routine for new articles
