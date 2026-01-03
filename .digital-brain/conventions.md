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

## Directory Structure

### Organization Principles
- **Flat top-level structure**: Top-level directories represent broad subject domains (content)
- **Infrastructure separation**: All system files live under `.digital-brain/` (hidden from content view)
- **No deep nesting**: Avoid subdirectories within content domains; use relationships and tags instead
- **Domain-based**: Directories organized by subject area, not by document type

### Content Domains
Content lives in top-level directories by subject:
- `concepts/` - Conceptual knowledge, definitions, frameworks
- `finance/` - Financial decisions, analyses, planning
- `fitness/` - Workout records, training plans, tracking
- `journal/` - Daily entries, reflections, decisions
- `media/` - External content consumption (books, articles, poetry, podcasts, videos)
- `people/` - People notes and relationships
- `projects/` - Project tracking and documentation
- `recipes/` - Recipe collection

### Infrastructure
All non-content files live under `.digital-brain/`:
- `conventions.md` - This file (governance rules)
- `relations.schema.json` - Relationship validation schema
- `indices/` - Auto-generated cross-cutting views
- `scripts/` - Automation tooling
- `templates/` - Note templates by type

### Rationale
**Decision** {date: 2026-01-03}: Adopted flat top-level structure over nested organization.

**Why flat over nested:**
- Simpler mental model: each domain is immediately visible
- Reduces friction: no decisions about "when to nest" or "when to promote"
- Better for growth: new domains added at top-level as needed
- Relationships over hierarchy: notes connect via explicit relations, not folder structure

**Why `.digital-brain/` for infrastructure:**
- Clear visual separation of content from tooling
- Follows `.git` convention (hidden but accessible)
- Keeps top-level clean and focused on subject domains

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
- **journal**: `[event]`, `[decision]`, `[todo]`
- **recipe**: `[definition]`, `[claim]`, `[question]`
- **finance**: `[event]`, `[decision]`, `[question]`
- **fitness**: `[event]`, `[decision]`, `[question]`
- **Cross-cutting**: `[event]` and `[decision]` can appear in any note type for tracking chronology and choices

## Observation Tag Semantics

### `[event]` vs `[decision]`

These two tags serve complementary but distinct purposes:

**`[event]`** - Records factual occurrences, actions taken, or things that happened
- Descriptive and chronological
- Documents what was done or what occurred
- No implication of choice between alternatives
- Examples:
  - `[event] {date: 2020-07-30} Front brake pads replaced at 159,574 km`
  - `[event] {date: 2008-03-31} Vehicle first registered in Switzerland`
  - `[event] {date: 2025-12-08} Completed routine inspection at Office cantonal des véhicules`

**`[decision]`** - Records explicit choices made between meaningful alternatives
- Implies agency and deliberation
- Documents why one option was chosen over another
- Represents strategic or tactical choices
- Examples:
  - `[decision] {date: 2025-03-15} Switched insurance to Baloise for better coverage`
  - `[decision] {date: 2024-06-10} Chose synthetic oil over conventional for cold weather performance`
  - `[decision] {date: 2025-01-15} Chose Vanguard VTI over individual stocks`

**Relationship**: `[decision]` is semantically a subtype of `[event]` - all decisions are events, but not all events are decisions.

**When unclear**: Ask "Were there meaningful alternatives I actively considered?"
- Yes → `[decision]`
- No/unclear → `[event]`

**Gray areas**: Routine maintenance at a default shop is an `[event]`; actively choosing Shop A over Shop B is a `[decision]`.

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
