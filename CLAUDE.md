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

## Interaction Modes: Quick vs Substantive Notes

When helping the user add notes, distinguish between two modes:

### Quick Notes - Be Autonomous
**Indicators:**
- Voice note transcripts or quick captures
- User says "just record this" or "dump this context"
- Brief, straightforward content
- Clear intent, minimal ambiguity

**Your approach:**
- Make reasonable choices autonomously
- Pick appropriate note type and location
- Structure observations logically
- Don't overthink or ask unnecessary questions
- Get it into the system efficiently
- Default to `[event]` for temporal facts, `[claim]` for properties

**Example:**
```
User: "Just note that I did a 30-minute run this morning at 7am"
You: [Creates fitness note with [event] observation, no questions asked]
```

### Substantive Notes - Be Consultative
**Indicators:**
- Significant detail or complexity
- Financial, strategic, or important decisions
- Multiple components or considerations
- User seems to be working through something
- Context that feels incomplete

**Your approach:**
- Pay attention to what's NOT explicitly stated
- Look for implied decisions that weren't called out
- Notice when alternatives existed but weren't mentioned
- Identify missing context that would be valuable
- Provide gentle nudges with questions

**What to look for:**
1. **Implied decisions**: "Switched to X" → Was there a choice between X and Y?
2. **Missing reasoning**: Why was this choice made?
3. **Observation type opportunities**:
   - Is this an `[event]` (what happened) or `[decision]` (choice made)?
   - Are there `[claim]` assertions about market conditions, expectations?
   - Should timing/context be captured with metadata?
4. **Timeline context**: Would dating this help track evolution of thinking?

**How to nudge:**
- Ask 1-2 focused questions, not a barrage
- Frame as "I noticed X, should we capture Y?"
- Suggest observation types: "This sounds like a decision between alternatives?"
- Offer to add context: "Want to note why you chose this approach?"
- Make it easy to decline: "Or I can just record it as-is"

**Example:**
```
User: [Provides detailed financial analysis with multiple considerations]
You: "I notice you're comparing fixed vs variable rates. This seems like a decision
between alternatives - want me to capture it as [decision] with the reasoning?
Also, those rate expectations sound like [claim] observations that might be worth
dating to track how your outlook evolves. Or I can just structure this as-is?"
```

### Heuristics for Mode Selection

**Quick Note if:**
- Under ~3 sentences
- Routine/recurring activity (workout, meal, etc.)
- User explicitly says "just..." or "quickly..."
- Single, clear fact to record

**Substantive Note if:**
- Financial/strategic importance
- Multiple paragraphs or complex structure
- Involves trade-offs or alternatives
- User is working through reasoning
- Feels like documentation vs capture

**When uncertain:** Default to autonomous (quick mode) and the user will tell you if they want more depth.

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
