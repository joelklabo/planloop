# planloop

Agent-first local planning loop that keeps AI coders synced with CI signals using
structured markdown plans. The source of truth for implementation work lives in
`docs/plan.md`.

## Requirements
- Python 3.11+
- `pip` 25+
- macOS or Linux shell (Windows support later)

## Setup
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## CLI Snapshot
The CLI is scaffolded with Typer commands (`status`, `update`, `alert`,
`describe`, `selftest`) that currently raise `NotImplementedCLIError`. Use
`planloop --help` (or `python -m planloop.cli --help`) to inspect the surface
area while implementation proceeds.

## Contributing
1. Read `docs/plan.md` for the current milestone and mark tasks IN_PROGRESS
   before editing code.
2. Use TDD when possible and never commit failing tests.
3. Keep commits small and reference the relevant task when updating the plan.
