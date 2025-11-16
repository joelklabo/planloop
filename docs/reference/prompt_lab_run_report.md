---
title: Prompt Lab Run Report
updated_at: 2025-11-16
---

# Prompt Lab Run Report

This log captures the prompt lab executions I ran locally with the real CLI adapters (Copilot CLI, OpenAI/Codex, Claude) so we can understand what is and isn’t working before we start optimizing prompts. Every invocation executed `labs/run_lab.py --scenario cli-basics --agents copilot,openai,claude` from the repo root with `PYTHONPATH=.:src` and the helper scripts under `labs/agents`. When a run needs more breathing room, I gave it a longer shell timeout (up to 600 s) because the agents spend several minutes running pytest and reasoning about the plan state.

## Run log

| Run | Variation | Summary | Agents | Result / Failure notes |
| --- | --- | --- | --- | --- |
| `20251116T041024Z` | Initial run before the `for adapter` loop was fixed | `labs/results/cli-basics-20251116T041024Z/summary.json` | openai only | `codex exec` complained about `--allow-tool` (it treated our prompt as a profile); the other adapters never ran because the loop dropped out after the first iteration. That prompted the `run_lab.py` indentation fix and a prompt to send the instructions as a positional argument instead of `-p`. |
| `20251116T041528Z` | After loop fix and before codex option cleanup | `labs/results/cli-basics-20251116T041528Z/summary.json` | copilot, openai, claude | Copilot ran but there was no `trace.log` (the wrappers still don’t log the structured trace). Codex exited with `unexpected argument '--allow-all-tools'`, so it never completed. Claude likewise failed on the unsupported `--no-browser`. These failures guided the flag cleanup. |
| `20251116T042329Z` | Flags cleaned up, 5 m timeout, signal inject and close | `labs/results/cli-basics-20251116T042329Z/summary.json` | copilot, openai (success); claude `exit code 1` | Codex finally completed (takes ~5 min, so the 480 s limit was just enough) but we still don’t emit `trace.log`, so compliance scoring always reports `score=0.0`. Claude still errored because both `--no-browser` and `--no-color` were unsupported. |
| `20251116T042947Z` | Removed `--no-browser`, `--no-color` from Claude script | `labs/results/cli-basics-20251116T042947Z/summary.json` | copilot & openai success; claude `exit code 1` | Claude dropped the `--no-browser` flag but now failed on `--no-color`. Another reminder that the CLI options change frequently and we have to align the wrappers with the shipped syntax. |
| `20251116T044241Z` | Current clean run with 600 s timeout + option fixes | `labs/results/cli-basics-20251116T044241Z/summary.json` | copilot, openai, claude (all success) | Every agent finished (Copilot <1 min, Codex ~5½ min, Claude ~2½ min). Compliance still reports `trace log missing` because the CLI wrappers do not create `trace.log` entries—mock agents do, but these real ones do not. This is the reference run we should compare future prompt tweaks against. |
| `20251116T085040Z` | Planloop now logs all status/update/alert calls for the real CLI adapters | `labs/results/cli-basics-20251116T085040Z/summary.json` | copilot, openai, claude (all success) | OpenAI/Codex and Claude now satisfy the compliance trace criteria (scores 70/80), but Copilot still never touches `planloop status`/`update` (no `trace.log`), so the scorer defaults to `trace log missing` for it. |

## Observations

1. **Trace logging is now automatic.** The CLI now appends `status`, `update`, and alert events to `<PLANLOOP_LAB_RESULTS>/<agent>/trace.log`, so real runs (Codex/Claude) can be scored without the mock agent. Copilot still never touches this API, so compliance remains 0 for that adapter until its wrapper synthesizes the trace entries.
2. **Command-line flags change rapidly.** Copilot and Codex both needed adjustments (we now run `copilot -p …` and `codex exec "$prompt" --sandbox workspace-write` without extra `--allow-*` flags), and Claude dropped `--no-browser` / `--no-color`. Every adapter script should be treated as brittle glue; new CLI versions will keep failing until we validate the options again.
3. **Long run time.** The successful run took ~557 s, so CI/workflows will need to allow at least 10 min for `labs/run_lab.py` (Codex spends 4‑6 min reasoning and running `python3 -m pytest`). The `timeout_ms` on the command must be large enough; otherwise the run dies before the agents finish.
4. **Trace scoring vs. real agents.** For now the compliance score is useless because the adapters don’t emit the required trace steps; we need to either log them ourselves or accept that the compliance metric is mocked until we wrap the real CLIs.

## Next steps

1. Extend the Copilot CLI wrapper so it either drives `planloop status/update/alert` commands itself or otherwise inserts the required `trace.log` entries (status/update/alert) before/after the run, because planloop already writes events when the CLI executes those commands.
2. Keep the adapter scripts aligned with shipping CLI syntax—if `codex exec` is updated again, revisit those options and rerun to verify the lab still behaves. A lint step that runs `codex --help` and verifies our flags exist might help catch future regressions.
3. Since the run takes ~10 min, update the GitHub Action/workflow (and any manual instructions) so the shell timeout is at least 600 s and we capture the artifacts (stdout/stderr/summary) even when the agent is still computing.
4. Use `labs/results/cli-basics-20251116T085040Z` as the benchmark artifact for prompt tuning; keep the summary JSON + trace log requirement front and center so we can compare new prompts’ behavior quantitatively instead of just “it completed.” 
