# planloop Prompt Lab – Detailed Execution Plan

## Goals

1. **Measure compliance** – capture whether each CLI agent (Copilot CLI, OpenAI/Codex, Claude) consistently follows the planloop workflow (status-first, blocker handling, structured updates).
2. **Support iteration** – make it easy to change the prompts and see when agents start misbehaving.
3. **Cover every agent/model** – exercise every CLI agent we can automate plus all relevant models they support (e.g., Copilot CLI, OpenAI gpt-4.1/gpt-4o/Codex, and Claude 3/2).
4. **Document the strategy** – include references (existing knowledge plus later web citations) so we can prove the lab design is grounded in best practices.

## Coverage Matrix

| Adapter | Models | Entry point | Env flag |
| --- | --- | --- | --- |
| Copilot CLI | GitHub Copilot CLI commands | `PLANLOOP_LAB_COPILOT_CMD` | `copilot` |
| OpenAI / Codex | gpt-4.1, gpt-4o, gpt-4o-mini, code-davinci-002 | custom Python runner | `openai` |
| Claude | Claude 3 / Claude 2 | Claude CLI or SDK script | `claude` |

Adjust the `labs/agents/command.py` adapter to call the specific binary or script pointed to by those env vars.

## Scenario workflow

1. Run `labs/run_lab.py --scenario cli-basics --agents copilot,openai,claude`.
2. The scenario seeds a session with two deterministic tasks and writes `state.json` + `PLAN.md`.
3. Each adapter receives the temp `PLANLOOP_HOME`, session ID, scenario name, workspace root, and results directory via environment variables.
4. Agents run their CLI logic and the adapter captures stdout/stderr plus compliance logs.

## Compliance measurements

1. **Status-first check** – confirm we logged `planloop status` before any `planloop update` or `alert`. Failure increments the “ignored status” counter.
2. **Blocker handling** – if `now.reason == ci_blocker`, ensure the agent intervenes on signals before touching tasks. Record violations when `planloop update` runs while blockers are open.
3. **Safe-mode enforcement** – when `safe_modes.update.no_plan_edit` or `strict` defaults are active, verify that structural edits never occur. Count failures when the agent adds/updates context or artifacts.
4. **Dry-run diff alignment** – compare `labs/results/.../dry_run.json` diff to the final `state.json`; if extra changes appeared, mark as “drift.”
5. **CLI command trace** – mirror the agent’s command sequence in a JSON log so we can replay or analyze it later.

Aggregate these into a per-run compliance score (`pass/fail` plus failure reasons) stored beside the agent’s summary JSON.

## Prompt iteration loop

1. Modify handshake/goal/summary prompts in `prompts/core-v1/*.prompt.md`.
2. Run the lab for all agents/models (`labs/run_lab.py --agents copilot,openai,claude`).
3. Inspect logs: summary JSON, dry-run diff, raw stdout/stderr.
4. If compliance score drops, tweak the prompts (e.g., add “always call status,” “only update tasks after blockers clear,” “never edit PLAN.md”) and rerun.
5. Repeat until all agents score “pass” on the scenario.

## Research & best practices (Task P4 focus)

1. **Survey published labs** – when web access is available, collect references from GitHub repos, blog posts, or docs describing how teams run Copilot/OpenAI/Claude in reproducible CLI labs. Note:
   * How they seed prompts + context.
   * How they capture command traces + logs.
   * Any scoring methodologies they use (e.g., step counts, blocker handling, compliance signals).
2. **Document findings** in this file (append a “Research references” section with URLs, summaries, and lessons we’ll adopt).
3. **Translate references into actions**:
   * Add metadata (agent name, model) to lab results.
   * Introduce thresholds (max commands, max blockers) inspired by referenced labs.
   * Expand scenarios (e.g., CI failure, coverage chain) based on the most representative workflows.

## Automation suggestions

1. **Daily/Manual runner** – add GitHub Actions (or manual script) that runs `labs/run_lab.py` nightly or on demand using real agent commands (with API keys stored as secrets). Upload logs/results for review.
2. **Result dashboard** – parse `labs/results/*/summary.json` to produce a table (agent/model, compliance score, failure reasons).
3. **Prompt regression gate** – require the lab to pass before merging prompt changes by including a script that runs the lab with simulated agents (or recorded responses).

## Next steps

1. Fill out the “Research references” section once we can browse the web.
2. Expand `labs/run_lab.py` and adapters with the measurement metrics above (status-first, blocker, dry-run diff).
3. Start iterating on prompts with each agent until compliance scores are consistently “pass,” then capture the successful prompt versions in the plan.
