---
set: core-v1
kind: summary
version: 0.1.0
description: >
  Guides agents when producing a final session summary and exit report.
---
# planloop Summary Prompt

Produce the final wrap-up for a session when all tasks and signals are closed.
Include the following sections:

1. **Completion Summary** – 2–3 sentences describing the overall result,
   referencing key features or fixes delivered. Mention the test suite / CI
   status.
2. **Task Outcomes** – Bulleted list highlighting each task ID and whether it
   shipped, was skipped, or changed scope.
3. **Signals Resolved** – Bullets referencing any CI/lint/system signals that
   were opened during the session and how they were addressed.
4. **Risks / Follow-ups** – Items that should become future tasks (if empty,
   write `- None`).

Keep the tone factual and reference file paths or PR numbers when relevant.
