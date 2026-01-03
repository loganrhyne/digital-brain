# CLAUDE.md - AI Assistant Context

## What This Is
Personal knowledge management system ("digital brain") for capturing, organizing, and connecting notes across multiple domains. Every document is a "note" regardless of content type.

## Directory Structure

### Content Domains (Top-Level)
```
├── concepts/        - Conceptual knowledge, definitions, frameworks
├── finance/         - Financial decisions, analyses, planning
├── fitness/         - Workout records, training plans, tracking
├── journal/         - Daily entries, reflections, decisions
├── media/           - External content consumption
│   ├── articles/    - Articles, podcast transcripts, video transcripts
│   ├── books/       - Book notes and observations
│   └── poetry/      - Poetry transcriptions with analysis
├── people/          - People notes and relationships
├── projects/        - Project tracking and documentation
└── recipes/         - Recipe collection with metadata
```

### Infrastructure (Hidden)
```
├── .digital-brain/
│   ├── conventions.md        - Complete formatting/structure rules
│   ├── relations.schema.json - JSON schema for relationship validation
│   ├── indices/              - Auto-generated cross-cutting views
│   ├── scripts/              - Automation (extract_decisions.py, rebuild_indices.py, etc.)
│   └── templates/            - Note templates by type
```

## Key Conventions

### Required Frontmatter
Every `.md` file must have YAML frontmatter:
```yaml
---
id: unique-identifier
type: concept|book|media|journal|recipe|fitness|poetry|finance|travel|meta
status: draft|active|archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
visibility: private|public
title: Human readable title
---
```

### Observation Types
Notes include an **Observations** section with typed bullets:
- `[definition]` - Definitions of terms/concepts
- `[claim]` - Assertions or arguments
- `[question]` - Questions raised
- `[decision]` - Decisions made (tracked globally)
- `[key-point]` - Important insights
- `[summary]` - Brief summaries
- `[application]` - Practical applications
- `[interpretation]` - Analysis or interpretation
- `[theme]` - Thematic elements

Observations support optional metadata:
```markdown
- [decision] {date: 2026-01-15} Chose this approach over alternatives
- [question] What's the optimal solution?
```

### Relationships
Relationships between notes encoded as JSON footnote objects:
```markdown
This connects to related concept[^1].

[^1]: {"relation": "builds-on", "target": "kb-2026-01-concept-id", "confidence": 0.9}
```

## Templates & Scripts

### Creating Notes
Templates in `.digital-brain/templates/` define structure for each note type. Use appropriate template when creating new notes.

### Automation
- `extract_decisions.py` - Scans all notes for `[decision]` observations, rebuilds `.digital-brain/indices/decisions.md`
- `rebuild_indices.py` - Regenerates all indices (books, concepts, media, poetry, recipes)
- `validate_relations.py` - Validates relationship footnotes against schema

### When to Rebuild Indices
After adding/modifying notes with observations, run relevant rebuild scripts to update indices.

## Common Workflows

### Adding a New Note
1. Use template from `.digital-brain/templates/{type}.md`
2. Fill in required frontmatter
3. Add observations with appropriate tags
4. Add relationship footnotes if relevant
5. Run rebuild scripts if needed

### Tracking Decisions
Any note can include `[decision]` observations. These are automatically extracted to `.digital-brain/indices/decisions.md` when you run `extract_decisions.py`.

### Organizing Principles
- **Flat structure**: Top-level directories are broad subject domains
- **Type-based templates**: Each content type has specific observation tags
- **Cross-cutting indices**: Indices aggregate specific observation types across all domains
- **Relationships over hierarchy**: Notes connect via footnote relations rather than deep folder nesting

## Important Files
- `.digital-brain/conventions.md` - Complete governance rules (defer to this for details)
- `.digital-brain/relations.schema.json` - Relationship validation schema
- `.digital-brain/indices/decisions.md` - Global decision tracking index
- `README.md` - User-facing repository description

## Note Type Specifics

### Media Notes
Include full transcripts for searchability. Required fields: `media_type`, `source_url`, `creator`, `published`, `duration_minutes`.

### Journal Notes
Daily entries with decisions and todos. Filename format: `YYYY-MM-DD.md`.

### Recipe Notes
Structured with ingredients, instructions, metadata (servings, time, difficulty).

## Future Considerations
- Handling embedded media files (photos, videos) in notes - not yet implemented
