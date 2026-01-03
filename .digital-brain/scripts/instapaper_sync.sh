#!/bin/bash
# Cron-compatible script to sync Instapaper articles to digital brain
#
# Usage:
#   ./instapaper_sync.sh [--dry-run] [--enrich] [--limit N]
#
# Crontab example (daily at 2 AM):
#   0 2 * * * /path/to/digital-brain/.digital-brain/scripts/instapaper_sync.sh >> /tmp/instapaper-sync.log 2>&1

set -euo pipefail

# Determine script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="${LOG_FILE:-/tmp/instapaper-sync-$(date +%Y%m%d).log}"

# Parse arguments
DRY_RUN=""
ENRICH=false
LIMIT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --enrich)
            ENRICH=true
            shift
            ;;
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
trap 'log "ERROR: Script failed at line $LINENO"' ERR

log "Starting Instapaper sync"
log "Repository: $REPO_ROOT"

# Check for Python
if ! command -v python3 &> /dev/null; then
    log "ERROR: python3 not found"
    exit 1
fi

# Check for required Python packages
if ! python3 -c "import requests, requests_oauthlib" 2>/dev/null; then
    log "ERROR: Required Python packages not installed"
    log "Install with: pip install requests requests-oauthlib"
    exit 1
fi

# Check for config file
CONFIG_FILE="$REPO_ROOT/.digital-brain/instapaper_config.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
    log "ERROR: Config file not found: $CONFIG_FILE"
    log "Copy instapaper_config.example.json to instapaper_config.json and configure"
    exit 1
fi

# Run import
log "Running import script..."
cd "$REPO_ROOT"

if python3 "$SCRIPT_DIR/instapaper_import.py" $DRY_RUN $LIMIT; then
    log "Import completed successfully"
else
    log "ERROR: Import failed"
    exit 1
fi

# Run AI enrichment if requested
if [[ "$ENRICH" == "true" ]]; then
    log "Running AI enrichment..."

    if python3 -c "import anthropic" 2>/dev/null; then
        if python3 "$SCRIPT_DIR/instapaper_enrich.py" $DRY_RUN; then
            log "Enrichment completed successfully"
        else
            log "WARNING: Enrichment failed (continuing)"
        fi
    else
        log "WARNING: Anthropic package not installed, skipping enrichment"
        log "Install with: pip install anthropic"
    fi
fi

log "Sync completed"

# If not dry run, show git status
if [[ -z "$DRY_RUN" ]]; then
    NEW_FILES=$(git ls-files --others --exclude-standard media/articles/instapaper-*.md 2>/dev/null | wc -l)
    if [[ $NEW_FILES -gt 0 ]]; then
        log "Created $NEW_FILES new article notes"
        log "Review and commit with: cd $REPO_ROOT && git add media/articles/ && git commit -m 'Add Instapaper articles'"
    else
        log "No new articles imported"
    fi
fi
