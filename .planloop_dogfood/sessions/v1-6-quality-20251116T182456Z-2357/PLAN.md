---
planloop_version: '1.5'
schema_version: 1
session: v1-6-quality-20251116T182456Z-2357
name: v1.6-quality
title: v1.6 Quality Improvements - Dogfooding Planloop
purpose: Improve planloop quality by dogfooding it to manage its own development.
  Add type checking, linting, coverage, and fix any UX issues discovered during real
  usage.
project_root: /Users/honk/code/planloop
branch: null
prompt_set: core-v1
created_at: '2025-11-16T18:24:56.797754'
last_updated_at: '2025-11-16T18:34:06.817738'
tags: []
environment:
  os: unknown
  python: null
  xcode: null
  node: null
---

# Plan: v1.6 Quality Improvements - Dogfooding Planloop

## Tasks
| ID | Title | Type | Status | Depends | Commit |
| --- | --- | --- | --- | --- | --- |
| 1 | Add mypy type checking to CI | feature | DONE | - | - |
| 2 | Add pytest-cov for test coverage reporting | feature | IN_PROGRESS | - | - |
| 3 | Add ruff linter to CI | feature | TODO | - | - |
| 4 | Dogfood planloop for 1 day - document all friction points | investigate | TODO | - | - |
| 5 | Fix top 3 UX issues from dogfooding | feature | TODO | 4 | - |

## Context
- UX Issue #1: update command silently swallows validation errors (cli.py:130-131)
- UX Issue #2: Schema not discoverable - needed to read code to understand add_tasks vs tasks
- UX Issue #3: last_seen_version must be string not int
- Mypy found 13 type errors to fix in follow-up work

## Next Steps
- Add pytest-cov to CI workflow
- Generate coverage report in CI
- Add coverage badge to README
- Set minimum coverage threshold

## Signals (Snapshot)
- _No signals_

## Agent Work Log
- _Not implemented yet_

## Artifacts
- _No artifacts recorded_

## Final Summary
_Not provided yet_
