---
id: kb-2026-01-conventions
type: meta
status: active
tags: [conventions, governance]
created: 2026-01-01
updated: 2026-01-02
visibility: private
title: Repository Conventions
---

# Repository Conventions

## Scope
These conventions define required structure and formatting for the digital-brain repo.

## Core Rules
- All .md files begin with YAML frontmatter containing id, type, status, created, updated, visibility.
- Substantive notes include an Observations section with typed bullets.
- Relationships are encoded as footnote JSON objects validated by `_meta/relations.schema.json`.

## Observation Metadata

Observations support optional metadata using inline object notation. Metadata appears immediately after the observation tag and before the observation text.

**Syntax**: `- [tag] {key: value, key2: value2} Observation text`

**Example**:
```markdown
- [decision] {date: 2026-01-15} Chose Vanguard VTI over individual stocks
- [question] What's the optimal rebalancing frequency?
```

**Guidelines**:
- Metadata is optional - observations without metadata remain valid
- Use curly braces `{}` to enclose metadata
- Separate multiple fields with commas
- Common metadata fields:
  - `date`: ISO date (YYYY-MM-DD) for when the observation occurred
  - Future: domain, confidence, priority, etc.
- Metadata enables richer indexing and filtering without cluttering observation text

**Common Observation Tags by Note Type**:
- **concept**: `[definition]`, `[claim]`, `[question]`
- **book**: `[definition]`, `[claim]`, `[question]`
- **poetry**: `[interpretation]`, `[theme]`, `[question]`
- **media**: `[summary]`, `[key-point]`, `[question]`, `[claim]`, `[application]`
- **journal**: `[decision]`, `[todo]`
- **recipe**: `[definition]`, `[claim]`, `[question]`
- **Cross-cutting**: `[decision]` can appear in any note type for tracking decisions in context

## Fair Use Policy for Poetry Transcription

Transcription of poems into this private digital brain repository constitutes fair use under U.S. copyright law (17 U.S.C. § 107) when:

- The poem was lawfully accessed (e.g., from a purchased book)
- The transcription is for personal use: reflection, learning, indexing, or cross-referencing
- There is no public redistribution, sale, or publication
- The use does not substitute for the original work

This is legally equivalent to writing a poem into a notebook, copying into research notes, or memorization. A digital knowledge repository is an extension of personal study and memory.

All four fair use factors support this use:
1. **Purpose**: Non-commercial, transformative (poem becomes informational object for cognition)
2. **Nature**: Creative works may be copied for non-expressive analytical purposes
3. **Amount**: Full copying permitted when purpose requires the whole work
4. **Market effect**: Private use does not diminish demand for the original

Poetry notes should always include proper attribution (poet, source collection) via footnote relations.

## Media Note Type

The **media** note type is for podcasts, videos, articles, and other multimedia content with full transcripts. This enables deep searchability and reference across different types of content.

### Required Fields
- `media_type`: Type of media (podcast, video, article, etc.)
- `source_url`: Original URL where content is available
- `creator`: Creator/author/host name(s)
- `published`: Publication date (ISO format)
- `duration_minutes`: Duration for audio/video content (omit for articles)

### Structure
Media notes follow the standard structure with these sections:
- **Observations**: Key points, summaries, questions using observation tags
- **Metadata**: Quick reference for type, creator, date, duration, source
- **Transcript**: Full verbatim transcript with speaker labels where applicable
- **Notes**: Personal reflections, connections, and analysis
- **Relations**: Links to related notes via footnote JSON

### Observation Tags for Media
- `[summary]` - Brief description of the content
- `[key-point]` - Important insights or arguments
- `[question]` - Questions raised by the content
- `[claim]` - Specific claims made
- `[application]` - Potential applications or implications

### Fair Use for Transcripts
Transcription of publicly available podcast/video content for personal knowledge management constitutes fair use when:
- Content is freely accessible or lawfully accessed
- Transcription is for personal study, reference, and note-taking
- No public redistribution occurs
- Attribution to original source is maintained
