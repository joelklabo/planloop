---
title: planloop – v1.5 Implementation Task Breakdown
version: 1.5
status: draft
owner: joel
created_at: 2025-11-15
updated_at: 2025-11-15
purpose: |
  Convert the v1.5 specification into discrete, commit-scale tasks that keep
  planloop's implementation on rails for both humans and AI agents.
tags:
  - agent-tools
  - local-dev
  - ios
  - ci
---

# Implementation Overview

`planloop` keeps AI coding agents inside a strict, CI-aware loop that is encoded
in `state.json` + `PLAN.md`. This document breaks the v1.5 spec into
chronological milestones populated with tasks sized for a single commit. Each
task below includes the scope, concrete deliverables, acceptance criteria, and
dependencies so we can move deliberately from an empty repo to a feature-complete
loop.

## Guardrails & Workflow Assumptions

- Treat this file as the work queue. Update the *Status* tags when a task is in
  flight or done, and include commit SHAs when closing items out.
- Practice TDD whenever practical: write or update tests first, make them pass,
  then refactor.
- Commit early and often, keeping changesets small. Never commit code that
  leaves tests failing.
- Before starting work on a task, mark it `IN_PROGRESS` here. When it is done
  and all tests pass, commit, push, and update the entry with the resulting
  commit reference plus any context learned.
- Always run the relevant test suite before committing; unfinished or failing
  work must stay local.
- Every task should result in code, docs, or tests that could ship in a single
  commit. If you feel tempted to split a task mid-flight, update this document
  before writing code.
- All commands must be safe for both humans and agents. Always keep
  PLANLOOP_HOME deterministic and avoid leaking project secrets into sessions.
- Tests accompany every behavior that can regress silently — especially state
  validation, CLI commands, locking, and self-tests.
- After finishing a task, immediately pick the next open TODO (respecting
  dependencies) and repeat the workflow.

## Milestones & Tasks

Each milestone is ordered to reduce rework. Unless otherwise noted, every task
starts in `Status: TODO` and depends on the tasks above it.

### Milestone 0 – Repository Foundations
> Goal: create a minimal but functional Python project that agents can install
> locally.

#### Task A1 – Bootstrap repo scaffolding *(Status: DONE – commit d07f0e8 "Bootstrap repo scaffolding (Task A1)")*

- **Scope:** Create `.gitignore`, LICENSE (MIT), README stub, `src/planloop/`,
  and `tests/` directories plus `src/planloop/__init__.py`.
- **Deliverables:** Clean repo tree, initial README with one-sentence project
  blurb, and empty `tests/__init__.py`.
- **Acceptance Criteria:** `git status` clean after commit; running `python -m
  planloop` fails gracefully because CLI is absent.
- **Dependencies:** none.

#### Task A2 – Add Python packaging baseline *(Status: DONE – commit 063de28 "Add packaging baseline (Task A2)")*
- **Scope:** Create `pyproject.toml` with Python 3.11+, runtime deps (`typer`,
  `textual`, `pydantic`, `pyyaml`, `jsonschema`, `rich`) and dev extras
  (`pytest`, `hypothesis`). Configure `planloop = planloop.cli:app` console
  script.
- **Deliverables:** `pyproject.toml`, `.python-version` (optional) and lock file
  ignored.
- **Acceptance Criteria:** `pip install -e .` succeeds; `python -m planloop.cli
  --help` prints Typer default help.
- **Dependencies:** Task A1.

#### Task A3 – CLI bootstrap *(Status: DONE – commit f6e0e47 "Stub CLI commands (Task A3)")*
- **Scope:** Implement `src/planloop/cli.py` exposing a Typer app with placeholder
  commands (`status`, `update`, `alert`, `describe`, `selftest`) that currently
  raise `NotImplementedError`.
- **Deliverables:** CLI entry point, `__main__.py`, smoke test verifying `planloop
  --help` works.
- **Acceptance Criteria:** `planloop --help` lists commands; `planloop status`
  exits with non-zero and prints "Not implemented".
- **Dependencies:** Task A2.

#### Task A4 – Developer onboarding docs *(Status: DONE – commit 4244c17 "Improve onboarding docs (Task A4)")*
- **Scope:** Expand README with install instructions, supported Python versions,
  and how to run the CLI in editable mode.
- **Deliverables:** README section covering `pip install -e .[dev]`, lint/test
  commands placeholder.
- **Acceptance Criteria:** A new contributor can bootstrap the project with only
  the README.
- **Dependencies:** Task A3.

### Milestone 1 – PLANLOOP_HOME & Configuration
> Goal: centralize state under `PLANLOOP_HOME` with repeatable initialization.

#### Task B1 – Implement PLANLOOP_HOME resolution *(Status: DONE – commit 8de34c3 "Implement PLANLOOP_HOME resolution (Task B1)")*
- **Scope:** Add `planloop/home.py` with `get_home()` that honors the
  `PLANLOOP_HOME` env var and defaults to `~/.planloop`.
- **Deliverables:** Function returning a `Path`, unit tests covering env override
  and default fallback.
- **Acceptance Criteria:** Calling `get_home()` creates the directory if needed
  and never raises for missing parents.
- **Dependencies:** Task A3.

#### Task B2 – Home initializer *(Status: DONE – commit 1c479cd "Initialize PLANLOOP_HOME layout (Task B2)")*
- **Scope:** Implement `initialize_home()` that populates `config.yml`,
  `sessions/`, `prompts/`, `messages/`, and `current_session` placeholder.
- **Deliverables:** Default `config.yml` (history flag, prompt set), directory
  scaffolding, helper invoked by CLI startup.
- **Acceptance Criteria:** Running `planloop status` in a fresh environment
  creates the expected tree with sane defaults.
- **Dependencies:** Task B1.

#### Task B3 – Seed default prompts & messages *(Status: DONE – commit 015705c "Seed prompts and messages (Task B3)")*
- **Scope:** Add `prompts/core-v1/*.prompt.md` and `messages/*.md` files with YAML
  front matter placeholders per the spec.
- **Deliverables:** `goal`, `handshake`, `summary`, `reuse_template` prompts plus
  `missing-docs-warning`, `reuse-template-info`, `onboarding-agent` messages.
- **Acceptance Criteria:** Loader can parse each file and capture metadata.
- **Dependencies:** Task B2.

### Milestone 2 – Session Data Model & PLAN.md Rendering
> Goal: define the canonical state representation and markdown renderer.

#### Task C1 – SessionState models *(Status: DONE – commit 9cf42ac "Add SessionState models (Task C1)")*
- **Scope:** Implement `core/state.py` with Pydantic models for `SessionState`,
  `Task`, `Signal`, `Artifact`, `Now`, etc., matching the schema in the spec.
- **Deliverables:** Data classes, enums for `task.status`, `task.type`,
  `signal.level`, etc.
- **Acceptance Criteria:** `SessionState.model_json_schema()` works; default state
  serializes/deserializes without mutation.
- **Dependencies:** Task B3.

#### Task C2 – Schema export & describe helpers *(Status: DONE – commit c7f3e66 "Add schema describe helpers (Task C2)")*
- **Scope:** Add `core/describe.py` that exports JSON Schemas for state and update
  payloads plus enumerations for `now.reason`, error codes, etc.
- **Deliverables:** Functions returning dicts, JSON fixtures for tests.
- **Acceptance Criteria:** `planloop describe --json` (stub) can call these
  helpers without raising.
- **Dependencies:** Task C1.

#### Task C3 – PLAN.md renderer & parser *(Status: DONE – commit ae8dba9 "Add PLAN.md renderer (Task C3)")*
- **Scope:** Implement `core/render.py` that converts `SessionState` into markdown
  with YAML front matter + sections (`Tasks`, `Context`, etc.) and can recover
  front matter when needed.
- **Deliverables:** Rendering code, golden-file tests that diff sample Markdown.
- **Acceptance Criteria:** Rendering + reparse round-trips the state fields used
  for display.
- **Dependencies:** Task C1.

### Milestone 3 – Session Lifecycle & Registry
> Goal: create, track, and switch between session workspaces under
> PLANLOOP_HOME.

#### Task D1 – Session ID + creation workflow *(Status: DONE – commit 4307ef6 "Add session creation helpers (Task D1)")*
- **Scope:** Build helpers that generate IDs (`<name>-<slug>-<timestamp>`),
  create `sessions/<id>/`, write initial `state.json`, render `PLAN.md`, and
  allocate `artifacts/`.
- **Deliverables:** `planloop session create` (or similar) CLI command, config to
  opt into per-session git history later.
- **Acceptance Criteria:** Running the command yields a session folder with
  populated files referencing prompt set + environment snapshot.
- **Dependencies:** Task C3.

#### Task D2 – Current-session pointer *(Status: DONE – commit e95d754 "Add current session pointer helpers (Task D2)")*
- **Scope:** Maintain `PLANLOOP_HOME/current_session` and commands to `set`,
  `show`, and `clear` it. Auto-populate when a new session is created.
- **Deliverables:** Helper functions + CLI options for `--session` fallback.
- **Acceptance Criteria:** `planloop status` without flags targets the pointer;
  pointer updates survive restarts. Track the simple pointer helpers now and add
  CLI wiring in Task G1 when `status` is implemented.
- **Dependencies:** Task D1.

#### Task D3 – Session index registry *(Status: DONE – commit 54bf184 "Add session registry helpers (Task D3)")*
- **Scope:** Implement `index.json` tracking metadata (name, tags, paths,
  timestamps, done flag). Update the file from session create/update flows.
- **Deliverables:** Registry module, read-modify-write utilities handling
  concurrency via locks.
- **Acceptance Criteria:** Listing the file shows every session once; stale
  entries get updated whenever `last_updated_at` changes.
- **Dependencies:** Task D1.

### Milestone 4 – Core Loop & State Validation
> Goal: compute `now.reason`, enforce invariants, and detect deadlocks.

#### Task E1 – Implement `compute_now` *(Status: DONE – commit 7eb160d "Implement compute_now (Task E1)")*
- **Scope:** Translate the algorithm from the spec into `core/state.py`, covering
  lock waits, blocker signals, in-progress tasks, ready todos, completion, and
  idle states.
- **Deliverables:** Pure function + unit tests.
- **Acceptance Criteria:** Tests cover blockers, dependency chains, completed
  plan scenarios.
- **Dependencies:** Task C1.

#### Task E2 – State validation & invariants *(Status: DONE – commit 2f9f599 "Add state validation (Task E2)")*
- **Scope:** Add validation routines ensuring unique task IDs, dependency
  integrity, matching `now` vs computed `now`, and optional cycle detection.
- **Deliverables:** `validate_state(state)` helper invoked by `status` and
  `update` paths.
- **Acceptance Criteria:** Invalid states raise descriptive errors with codes for
  agents; tests cover regressions.
- **Dependencies:** Task E1.

#### Task E3 – Deadlock detection *(Status: DONE – commit a8a7008 "Add deadlock detection (Task E3)")*
- **Scope:** Track `last_state_hash` + `no_progress_counter` in state or
  sidecar. When repeated `status` calls occur without updates, open a
  `system/deadlock_suspected` signal and set `now.reason = deadlocked`.
- **Deliverables:** Counter logic, signal injection helper, tests simulating
  deadlock threshold. Store counters in a lightweight tracker persisted next to
  `SessionState` until we add better metadata support.
- **Acceptance Criteria:** After N idle cycles, status output changes reason and
  surfaces guidance text.
- **Dependencies:** Task E2.

### Milestone 5 – Serialized Access & Lock Surfacing
> Goal: ensure writes are serialized and lock information is visible.

#### Task F1 – Lock acquisition helpers *(Status: DONE – commit e18762c "Add session lock helpers (Task F1)")*
- **Scope:** Implement cross-platform `.lock` handling with owner metadata and
  timeout safeguards for every write path.
- **Deliverables:** `lock.py` module with `acquire_lock`, `release_lock`, and
  context manager; tests using temp dirs.
- **Acceptance Criteria:** Concurrent write attempts block (or fail fast) and
  never leave dangling locks on crash.
- **Dependencies:** Task D1.

#### Task F2 – Lock info in status *(Status: DONE – commit c2b1871 "Surface lock status helper (Task F2)")*
- **Scope:** Extend `status` output with `now.reason = waiting_on_lock` plus
  `lock_info` + human-readable instructions when the lock is held.
- **Deliverables:** Formatting code for CLI + JSON output, doc updates.
- **Acceptance Criteria:** `planloop status --json` returns lock metadata when a
  lock file exists.
- **Dependencies:** Task F1.

### Milestone 6 – Agent-Facing CLI Commands
> Goal: deliver the core commands (`status`, `update`, `alert`, `describe`) with
> strict schemas.

#### Task G1 – `planloop status` implementation *(Status: DONE – commit 36db4a7 "Implement status command (Task G1)")*
- **Scope:** Wire CLI to load the session, run validation, recompute `now`, and
  print either pretty tables or JSON. Include `agent_instructions` guidance.
  Depends on session pointer, registry, lock info, and deadlock tracker. For
  now we will output JSON only with a clear structure.
- **Deliverables:** `status` command, JSON output tests, and helper to load the
  requested session (current pointer fallback).
- **Acceptance Criteria:** Fake sessions return deterministic JSON consumed by
  future agents. Lock info is surfaced when present.
- **Dependencies:** Task E2.

#### Task G2 – Structured `update` command *(Status: DONE – commit cf1fc97 "Implement update command (Task G2)")*
- **Scope:** Define update payload schema, validate `last_seen_version`, merge
  changes (task updates, adds, context notes, next steps, artifacts, final
  summary), and persist `state.json` + `PLAN.md` under lock.
- **Deliverables:** `core/update.py`, CLI plumbing, schema-driven error messages.
- **Acceptance Criteria:** Passing a valid JSON payload mutates state and bumps
  version; invalid payloads return machine-readable errors.
- **Dependencies:** Task G1, Task F1.

#### Task G3 – `planloop alert` signals API *(Status: DONE – commit fb815e6 "Add alert command (Task G3)")*
- **Scope:** Provide CLI for opening/closing signals (CI, lint, etc.), update
  state + tasks, and ensure blockers immediately affect `now.reason`.
- **Deliverables:** CLI command, helper for deduping signals, doc updates about
  plugin usage. For now, support basic `open` and `close` operations with JSON
  output.
- **Acceptance Criteria:** Opening a blocker signal changes `now.reason` to
  `ci_blocker`; closing it reverts to task workflow.
- **Dependencies:** Task G2.

#### Task G4 – `planloop describe` command *(Status: TODO)*
- **Scope:** Surface schemas from Task C2 plus enumerations and sample payloads
  so advanced agents can introspect.
- **Deliverables:** CLI command writing JSON to stdout, test comparing expected
  schema snapshot.
- **Acceptance Criteria:** Command returns valid JSON referencing every schema
  field described in the spec.
- **Dependencies:** Task C2.

#### Task G5 – Session management CLI wrappers *(Status: TODO)*
- **Scope:** Add user-facing commands like `planloop sessions list`, `planloop
  sessions info`, `planloop sessions delete` (non-destructive), wired into
  registry.
- **Deliverables:** CLI subcommands + doc updates.
- **Acceptance Criteria:** Listing shows metadata from `index.json`; info command
  points to session paths.
- **Dependencies:** Task D3.

### Milestone 7 – Search & Template Reuse
> Goal: help operators discover prior sessions and reuse good patterns.

#### Task H1 – Search implementation *(Status: TODO)*
- **Scope:** Add `planloop search <query>` that tokenizes the query and matches
  across name/title/tags/project_root fields in `index.json`.
- **Deliverables:** Search module, CLI command, tests for ranking + case
  insensitivity.
- **Acceptance Criteria:** Searching "ios crash" returns relevant sessions in a
  stable order.
- **Dependencies:** Task D3.

#### Task H2 – Template listing *(Status: TODO)*
- **Scope:** Provide `planloop templates` that filters sessions with
  `done == true` and optional `good_template` tag.
- **Deliverables:** CLI table or JSON, docs explaining how to flag templates.
- **Acceptance Criteria:** Only qualifying sessions appear; output includes tags
  and summaries.
- **Dependencies:** Task H1.

#### Task H3 – Template reuse workflow *(Status: TODO)*
- **Scope:** Implement `planloop reuse <session>` that injects the referenced
  session's summary/tasks into prompt context (`reuse_template.prompt.md`) and
  guides the user through naming a new goal.
- **Deliverables:** CLI wizard, prompt rendering logic, message from
  `reuse-template-info.md`.
- **Acceptance Criteria:** Running the command produces a ready-to-use context
  blob or writes to the goal prompt as designed.
- **Dependencies:** Task B3, Task H2.

### Milestone 8 – Prompts, Messages & Agent Contract
> Goal: externalize agent instructions and integrate with project docs.

#### Task J1 – Prompt/message loader *(Status: TODO)*
- **Scope:** Implement `core/prompts.py` to read files with YAML front matter,
  validate required fields, and expose content keyed by set/kind.
- **Deliverables:** Loader functions, caching, error handling for missing sets.
- **Acceptance Criteria:** CLI commands can request prompts without repeated disk
  reads.
- **Dependencies:** Task B3.

#### Task J2 – Author core prompt content *(Status: TODO)*
- **Scope:** Fill `goal`, `handshake`, `summary`, `reuse_template` files with the
  agent contract described in the spec (status-first workflow, JSON payloads,
  blocker priority, etc.).
- **Deliverables:** Well-written prompt copy referencing schema expectations and
  behavioral rules.
- **Acceptance Criteria:** Content passes lint (no tabs, <100 char lines) and
  includes version metadata in front matter.
- **Dependencies:** Task J1.

#### Task J3 – `planloop guide` + docs injection *(Status: TODO)*
- **Scope:** Build `planloop guide --target agents-md` that renders instructions
  for AGENTS.md. Detect missing `<!-- PLANLOOP-INSTALLED -->` markers and surface
  `missing-docs-warning.md`, optionally auto-appending guidance.
- **Deliverables:** CLI command, helper that finds AGENTS.md / Copilot configs.
- **Acceptance Criteria:** Running `planloop guide` prints markdown referencing
  prompts + handshake contract; repeated runs avoid duplicate insertion.
- **Dependencies:** Task J2.

### Milestone 9 – TUI & Web UI
> Goal: provide read-only dashboards for sessions.

#### Task K1 – Textual TUI dashboard *(Status: TODO)*
- **Scope:** Implement `planloop view` that launches a Textual app showing task
  table, signals, lock info, context notes, and work log.
- **Deliverables:** `tui/app.py`, layout components, keyboard shortcuts.
- **Acceptance Criteria:** Running the command renders the latest session data
  and reacts to window resize without crashing.
- **Dependencies:** Task G1.

#### Task K2 – Web view *(Status: TODO)*
- **Scope:** Provide `planloop web` using Textual's web server or a minimal
  FastAPI app to display the same data in a browser.
- **Deliverables:** Web entry point, session picker page, session detail page.
- **Acceptance Criteria:** Starting the command prints a local URL; hitting it in
  a browser shows the same data as the TUI.
- **Dependencies:** Task K1.

### Milestone 10 – History, Snapshots & Rollback
> Goal: optionally track per-session history using embedded git.

#### Task L1 – Optional per-session git repos *(Status: TODO)*
- **Scope:** When `history.enabled` is true, initialize a git repo under each
  session, configure `.gitignore`, and commit `state.json` + `PLAN.md` on writes.
- **Deliverables:** History settings in config, helper invoked from update/alert
  flows.
- **Acceptance Criteria:** Running updates creates commits with descriptive
  messages and retains history even if the main repo isn't tracked.
- **Dependencies:** Task D1, Task G2.

#### Task L2 – Snapshot command *(Status: TODO)*
- **Scope:** Implement `planloop snapshot` that creates a git commit/tag and
  returns an ID.
- **Deliverables:** CLI command, message summarizing snapshot contents.
- **Acceptance Criteria:** Command outputs snapshot hash and records it in the
  session log.
- **Dependencies:** Task L1.

#### Task L3 – Restore command *(Status: TODO)*
- **Scope:** Add `planloop restore <snapshot>` that resets the session repo to a
  commit, rewrites `state.json`/`PLAN.md`, and recomputes `now`.
- **Deliverables:** CLI command with safety checks (confirmation prompt when
  work-in-progress exists).
- **Acceptance Criteria:** After restoring, `planloop status` reflects the older
  state; artifacts dir remains untouched.
- **Dependencies:** Task L2.

### Milestone 11 – Testing & Self-Test Harness
> Goal: guarantee behaviors with unit tests, integration tests, and an automated
> selftest runner.

#### Task M1 – Core unit tests *(Status: TODO)*
- **Scope:** Add pytest modules for `state.compute_now`, `validate_state`,
  `render`, and prompts loader. Use Hypothesis where valuable.
- **Deliverables:** Tests + fixtures under `tests/` with coverage for edge cases
  (dependency loops, signals, env detection).
- **Acceptance Criteria:** `pytest tests/test_state.py` etc. pass locally and in
  CI.
- **Dependencies:** Tasks C1–C3, E2.

#### Task M2 – CLI integration tests *(Status: TODO)*
- **Scope:** Use `tmp_path` to simulate PLANLOOP_HOME, create sample sessions,
  and exercise CLI commands end-to-end (`status`, `update`, `alert`).
- **Deliverables:** Integration test module plus helper to invoke CLI via Typer's
  test runner.
- **Acceptance Criteria:** `pytest tests/test_cli_loop.py` passes and verifies
  JSON output schema.
- **Dependencies:** Tasks G1–G3.

#### Task M3 – `planloop selftest` command *(Status: TODO)*
- **Scope:** Implement the fake-agent harness described in the spec: create temp
  home, run scripted workflows (CI failure, clean run, coverage scenario), and
  assert invariants.
- **Deliverables:** `core/selftest.py`, CLI command, fixtures for sample tasks.
- **Acceptance Criteria:** `planloop selftest` exits 0 locally without network or
  LLM usage.
- **Dependencies:** Task M2.

### Milestone 12 – Logging & Debug Tools
> Goal: capture useful logs per session and expose a debug command.

#### Task N1 – Logging infrastructure *(Status: TODO)*
- **Scope:** Configure `logging.getLogger("planloop")` with handlers that write
  to `sessions/<id>/logs/planloop.log` and optionally stdout.
- **Deliverables:** Logging config module, integration with CLI commands, log
  rotation policy.
- **Acceptance Criteria:** Every command logs key lifecycle events (locks,
  updates, errors) without leaking secrets.
- **Dependencies:** Task G1.

#### Task N2 – `planloop debug` command *(Status: TODO)*
- **Scope:** Add CLI to dump `state.json`, PLAN path, open signals, last commits,
  and lock/deadlock info.
- **Deliverables:** Command outputting structured text/JSON, docs describing use.
- **Acceptance Criteria:** Command helps humans triage issues without poking
  internal files manually.
- **Dependencies:** Task N1.

### Milestone 13 – Safe Modes & Advanced Update Options
> Goal: provide guardrails for human debugging and strict agents.

#### Task O1 – Update dry-run mode *(Status: TODO)*
- **Scope:** Add `planloop update --dry-run` that parses payloads, displays the
  planned diff, and exits without writing.
- **Deliverables:** Diff generator for state/task changes, CLI flag handling.
- **Acceptance Criteria:** Dry runs exit 0 without touching files and show
  user-friendly diffs.
- **Dependencies:** Task G2.

#### Task O2 – Strict + limited update modes *(Status: TODO)*
- **Scope:** Implement `--no-plan-edit` (only status changes allowed) and
  `--strict` (reject unknown fields) flags.
- **Deliverables:** Flag plumbing, error reporting, docs explaining safe modes.
- **Acceptance Criteria:** Violating the mode returns explict errors and leaves
  state untouched.
- **Dependencies:** Task O1.

---

## Next Steps
1. Execute Task A1 to get the repository skeleton in place.
2. Keep this document updated (status tags, new tasks, reprioritization) as the
   implementation progresses.
