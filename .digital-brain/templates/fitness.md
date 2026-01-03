---
id: "{{id}}"
type: fitness
status: draft
tags: [fitness, "{{domain}}"]
created: "{{created}}"
updated: "{{updated}}"
visibility: private
title: "{{title}}"
---

# {{title}}

## Observations
<!-- Use [event] for workout instances - what you did and when -->
- [event] {date: {{date}}, time: "{{time}}", location: "{{location}}"} Completed {{workout_type}} workout
<!-- Use [decision] for training choices - why you chose one approach over another -->
- [decision] {date: {{date}}} {{decision}}
<!-- Use [claim] for workout details/metadata without dates -->
- [claim] {equipment: "{{equipment}}", rounds: {{rounds}}} {{claim}}
<!-- Use [question] for training questions or areas to investigate -->
- [question] {{question}}

## Notes
{{notes}}
