# Lab Testing Guide

**Purpose**: Testing real AI agents for planloop workflow compliance

## Overview

The lab infrastructure tests real agent CLIs (GitHub Copilot, Claude, etc.) against planloop workflow scenarios to measure compliance and guide prompt optimization.

## Current Performance

**As of 2025-11-17** (158 total runs):
- **Copilot (gpt-5)**: 64.3% pass rate, 51.5/100 avg score ✅
- **Claude (sonnet)**: 29.3% pass rate, 32.2/100 avg score
- **OpenAI**: 33.3% pass rate, 17.9/100 avg score

See `docs/agent-performance.md` for latest metrics.

## Architecture

### Real Agent Adapters
Located in `labs/agents/`:
- `copilot_real.sh` - Invokes GitHub Copilot CLI with trace logging
- `claude_real.sh` - Invokes Claude CLI with trace logging
- `command.py` - Common adapter infrastructure

**Key Requirements**:
- Capture stdout/stderr from agent
- Generate `trace.log` with command history
- Extract model name from agent output
- Handle agent-specific quirks (streaming, colors, etc.)

### Scenarios
Located in `labs/scenarios/`:
- `cli-basics.py` - 2 tasks + 1 CI blocker signal (baseline test)

**Future scenarios** (when baseline >60%):
- `multi-signal-cascade` - 5 tasks, 3 signals at different stages
- `dependency-chain` - Tasks with complex dependencies
- `full-plan-completion` - Realistic 12-task feature implementation

### Evaluation
`labs/evaluate.py` checks:
- ✅ All tasks completed
- ✅ Status called after every update
- ✅ Signals properly handled and cleared
- ✅ Trace log completeness

**Scoring**: 0-100 based on workflow compliance

## Running Tests

### Single Run
```bash
cd /Users/honk/code/planloop
python labs/run_lab.py --scenario cli-basics --agents copilot
```

### Batch Iterations
```bash
# Run 10 iterations with copilot
./labs/run_iterations.sh 10 cli-basics copilot

# Multiple agents
./labs/run_iterations.sh 10 cli-basics copilot,claude
```

### View Results
```bash
# Aggregate metrics
python labs/aggregate_metrics.py

# Generate visualization
python labs/generate_viz.py

# View performance report
cat docs/agent-performance.md
```

## Metrics Tracked

**Per Agent+Model**:
- Pass rate (% of runs achieving 100% compliance)
- Average score (0-100)
- Top error patterns
- Model version used

**Quality Metrics**:
- Task completion percentage
- Signal handling correctness
- Status usage patterns
- Update correctness

## Optimization Strategy

1. **Establish Baseline**: Test real agents on simple scenario
2. **Analyze Failures**: Identify common error patterns
3. **Iterate Prompts**: Improve agent instructions based on data
4. **Measure Impact**: Track score improvements over time
5. **Increase Difficulty**: Add harder scenarios when ready (>60% baseline)

## Key Learnings

**What Works**:
- Step-by-step instructions better than narrative
- Explicit stop conditions required
- JSON payload examples help
- Clear workflow loop structure

**Common Failures**:
- Missing status calls after updates
- Not clearing blocker signals
- Stopping before all tasks complete
- Incorrect JSON payload format

## Files

- `labs/run_lab.py` - Main test runner
- `labs/run_iterations.sh` - Batch testing script
- `labs/aggregate_metrics.py` - Metrics aggregation
- `labs/generate_viz.py` - Performance visualization
- `labs/evaluate.py` - Compliance scoring
- `labs/metrics.json` - Historical metrics data
- `docs/agent-performance.md` - Latest results (auto-generated)

## Checking for Rate Limits

Rate limits can cause test failures that look like prompt issues. Check for them:

```bash
./labs/check_rate_limits.sh
```

This scans all test results and reports:
- Which agents hit limits
- When limits were hit
- Links to usage settings

### Rate Limit Indicators

Each agent adapter detects rate limits automatically:

- **Codex**: "usage limit", "purchase more credits"
- **Claude**: "session limit", "rate limit"  
- **Copilot**: "rate limit", "quota exceeded"

When detected:
- Returns exit code 2 (distinct from other failures)
- Logs `rate_limit_exceeded` trace event
- Shows clear warning message

### Handling Rate Limits

If you hit a rate limit:

1. Note the reset time from error message
2. Exclude those runs from metrics analysis
3. Wait for quota to reset before retesting

**Example**: Codex Nov 17, 2025:
- 9 runs hit usage limit starting at 3:11am
- Reset scheduled for Nov 20, 2025 9:22am
- Performance appeared to decline but was actually limit errors
