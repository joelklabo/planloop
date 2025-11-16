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
last_updated_at: '2025-11-16T18:42:26.353097'
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
| 2 | Add pytest-cov for test coverage reporting | feature | DONE | - | - |
| 3 | Add ruff linter to CI | feature | DONE | - | - |
| 4 | Dogfood planloop for 1 day - document all friction points | investigate | DONE | - | - |
| 5 | Fix top 3 UX issues from dogfooding | feature | IN_PROGRESS | 4 | - |

## Context
- Testing int version coercion

## Next Steps
- Fix #1: Print validation errors in update command
- Fix #2: Add helpful error message for schema issues
- Fix #3: Accept both string and int for version field

## Signals (Snapshot)
- _No signals_

## Agent Work Log
- _Not implemented yet_

## Artifacts
- _No artifacts recorded_

## Final Summary
_Not provided yet_
