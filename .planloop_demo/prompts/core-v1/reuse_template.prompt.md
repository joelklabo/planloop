---
set: core-v1
kind: reuse_template
version: 0.1.0
description: >
  Provides context when bootstrapping a new session from a previous template.
---
# planloop Template Reuse Prompt

You are preparing context so a new planloop session can reuse a past template.
Respond with:

1. **Why this template** – 1–2 sentences describing what makes the referenced
   session a good example (tech stack, workflow style, test strategy).
2. **Key Tasks to Mirror** – Bullet list summarizing 3–5 tasks from the
   template that the next agent should follow, with short rationale for each.
3. **Adjustments Needed** – Bullet list describing what must change to adapt
   the template to the new goal (optional if nothing differs).

Use short Markdown bullets and avoid copying large diffs; the goal is to give
the next agent a crisp recipe inspired by the previous success.
