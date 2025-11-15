---
set: core-v1
kind: goal
version: 0.1.0
description: >
  Placeholder goal prompt guiding agents to gather project context and produce
  a plan before coding.
---
# planloop Goal Prompt

You are preparing instructions for an AI coding agent that will use
`planloop` to implement a project. Respond with:

1. **Summary** – One paragraph that restates the goal, success criteria, and
   notable constraints (platforms, deadlines, CI requirements, stakeholders).
2. **Signals** – Bulleted list of known blockers/risk signals. Include CI or
   lint references when provided. If none exist, write `- None reported`.
3. **Initial Tasks** – Numbered list of commit-sized tasks that follow the
   planloop workflow (TDD, small increments, green tests). Each task should
   include:
   - short imperative title,
   - success definition or exit criteria,
   - obvious dependencies on earlier tasks.
4. **Open Questions** – Any clarifications the agent should raise before
   coding (optional).

Keep the response under 350 words. Use concise Markdown and avoid code unless
the user explicitly asks for scaffolding.
