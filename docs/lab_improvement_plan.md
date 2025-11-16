# Lab Infrastructure Deep Analysis & Improvement Plan

**Created**: 2025-11-16T20:46:00Z  
**Status**: In Progress  
**Goal**: Achieve realistic agent compliance metrics through iterative testing and prompt optimization

## Executive Summary

Our lab currently shows 100% compliance with mock agents but only 22-33% with historical data. This disconnect reveals we're not testing against real agent behavior. This plan outlines a systematic approach to:
1. Test real agent CLIs (not mocks)
2. Create progressively harder scenarios
3. Track model-specific performance
4. Iteratively optimize prompts based on data

## Current State

### Available Real Agents
- ✅ **GitHub Copilot CLI** (`copilot` v0.0.358) - Available locally
- ✅ **Claude CLI** (`claude` v2.0.42) - Available locally
- ❓ **OpenAI/ChatGPT CLI** - Need to verify availability
- ❓ **Aider** - Could add as bonus agent

### Current Scenario (cli-basics)
- **Tasks**: Only 2 simple tasks
- **Signals**: Single CI blocker injection
- **Complexity**: Too easy - agents achieve 100% mock compliance
- **Duration**: ~2-3 seconds to complete
- **No verification**: Doesn't check if ALL tasks completed

### Current Metrics Gaps
- ❌ Not tracking which model each agent uses
- ❌ Not verifying task completion percentage
- ❌ No workflow quality metrics (excessive status calls, etc.)
- ❌ No failure pattern analysis
- ❌ Testing mocks instead of real agents

## Implementation Plan

### Phase 1: Real Agent Infrastructure (IMMEDIATE - This Week)

#### Step 1.1: Test Real Agents Individually
**Goal**: Verify each agent CLI works and understand its quirks

```bash
# Test GitHub Copilot CLI
copilot -p "Check planloop status and update task 1 to IN_PROGRESS" \
  --allow-all-tools --allow-all-paths --no-color

# Test Claude CLI  
claude -p "Check planloop status and update task 1 to IN_PROGRESS" \
  --print --allowedTools "Bash"
```

**Deliverable**: Document each agent's:
- Required flags for non-interactive execution
- How to extract model information
- Output format and trace requirements
- Any authentication needs

#### Step 1.2: Create Real Agent Adapter Scripts
**Goal**: Replace mock_agent.sh usage with real CLI invocations that generate trace logs

**Files to Create/Modify**:
1. `labs/agents/copilot_real.sh` - Invokes copilot CLI with instrumentation
2. `labs/agents/claude_real.sh` - Invokes claude CLI with instrumentation  
3. `labs/agents/trace_wrapper.sh` - Shared trace logging for all adapters

**Key Requirements**:
- Capture stdout/stderr from agent
- Generate trace.log with same format as mock agent
- Extract model name from agent output/config
- Handle agent-specific quirks (streaming, colors, etc.)

#### Step 1.3: Add Model Detection
**Goal**: Track which specific model each agent uses

**Changes**:
- Modify `labs/agents/command.py` to capture model info
- Update `labs/run_lab.py` to include model in summary.json
- Extend `labs/aggregate_metrics.py` to group by agent+model
- Add model field to `docs/agent-performance.md`

**Expected Output**:
```json
{
  "agent": "copilot",
  "model": "gpt-4o",
  "compliance": {"score": 75.0}
}
```

### Phase 2: Enhanced Scenarios (Week 1-2)

#### Scenario 2.1: multi-signal-cascade (Medium Difficulty)
**Purpose**: Test signal priority handling with multiple blockers

```python
# 5 tasks, 3 signals appearing at different stages
tasks = [
    Task(id=1, title="Setup project structure"),
    Task(id=2, title="Implement core logic", depends_on=[1]),
    Task(id=3, title="Add error handling", depends_on=[2]),
    Task(id=4, title="Write unit tests", type=TEST, depends_on=[3]),
    Task(id=5, title="Update documentation", type=DOCS, depends_on=[4]),
]

# Inject signals at specific progress points:
# - After task 1 done: CI blocker
# - After CI cleared: Lint blocker
# - After task 4 done: Bench warning (non-blocking)
```

**Success Criteria**:
- Agent handles all blockers before proceeding
- Agent completes all 5 tasks
- Correct task ordering (no dependency violations)

#### Scenario 2.2: dependency-chain (Medium Difficulty)
**Purpose**: Test complex dependency resolution

```python
# 8 tasks with diamond dependencies
tasks = [
    Task(id=1, title="Create API client"),
    Task(id=2, title="Add auth module", depends_on=[1]),
    Task(id=3, title="Add data module", depends_on=[1]),
    Task(id=4, title="Implement GET endpoints", depends_on=[2, 3]),
    Task(id=5, title="Implement POST endpoints", depends_on=[2, 3]),
    Task(id=6, title="Add rate limiting", depends_on=[4, 5]),
    Task(id=7, title="Write integration tests", depends_on=[6]),
    Task(id=8, title="Update API docs", depends_on=[7]),
]

# 2 signals: one blocks task 4, another blocks task 6
```

#### Scenario 2.3: full-plan-completion (Hard Difficulty)
**Purpose**: Test stamina and autonomous task completion

```python
# 12 tasks representing realistic feature implementation
tasks = [
    # Setup phase (3 tasks)
    Task(id=1, title="Create feature branch"),
    Task(id=2, title="Add config schema", depends_on=[1]),
    Task(id=3, title="Update environment setup", depends_on=[2]),
    
    # Implementation phase (4 tasks)
    Task(id=4, title="Implement core feature", depends_on=[3]),
    Task(id=5, title="Add validation logic", depends_on=[4]),
    Task(id=6, title="Implement error handling", depends_on=[5]),
    Task(id=7, title="Add logging and metrics", depends_on=[6]),
    
    # Testing phase (3 tasks)
    Task(id=8, title="Write unit tests", type=TEST, depends_on=[7]),
    Task(id=9, title="Write integration tests", type=TEST, depends_on=[8]),
    Task(id=10, title="Add edge case tests", type=TEST, depends_on=[9]),
    
    # Finalization (2 tasks)
    Task(id=11, title="Update documentation", type=DOCS, depends_on=[10]),
    Task(id=12, title="Update changelog", type=DOCS, depends_on=[11]),
]

# 4 signals appearing throughout:
# - After task 3: CI blocker
# - After task 6: Lint blocker
# - After task 9: Coverage warning (non-blocking)
# - After task 11: Security scan (blocking)
```

**Success Criteria**:
- Agent completes ALL 12 tasks (100% completion)
- Handles all 4 signals correctly
- Maintains proper task order
- Doesn't give up mid-way

#### Scenario Implementation
**Files to Create**:
- `labs/scenarios/multi_signal_cascade.py`
- `labs/scenarios/dependency_chain.py`
- `labs/scenarios/full_plan_completion.py`
- `labs/scenarios/__init__.py` - Update with new scenarios

**Scenario Metadata**:
```python
@dataclass
class Scenario:
    name: str
    difficulty: str  # "simple", "medium", "hard"
    description: str
    expected_tasks: int
    expected_signals: int
    timeout_seconds: int  # Prevent infinite loops
```

### Phase 3: Advanced Metrics (Week 2-3)

#### Metric 3.1: Task Completion Tracking
**Goal**: Verify agents finish what they start

**New Metrics**:
```python
{
    "tasks_total": 12,
    "tasks_completed": 8,
    "completion_rate": 0.67,
    "tasks_in_progress": 2,
    "tasks_blocked": 2,
    "final_state": "incomplete"  # or "complete"
}
```

**Implementation**:
- Add `verify_task_completion()` to run_lab.py
- Check final session state after agent finishes
- Penalize incomplete runs in compliance score

#### Metric 3.2: Signal Handling Quality
**Goal**: Measure blocker response quality

**New Metrics**:
```python
{
    "signals_opened": 3,
    "signals_closed": 3,
    "avg_close_time_seconds": 15.2,
    "blocker_violations": 0,  # Updates while blocker active
    "missing_status_rerun": 1  # Didn't verify after closing
}
```

#### Metric 3.3: Workflow Quality
**Goal**: Identify inefficient patterns

**New Metrics**:
```python
{
    "status_calls": 15,
    "update_calls": 10,
    "status_per_update": 1.5,  # Ideal is ~1-2
    "excessive_polling": false,
    "updates_without_status": 2  # Should be 0
}
```

#### Metric 3.4: Model-Specific Analysis
**Goal**: Compare models within same agent

**Grouping**:
```python
results_by_model = {
    "copilot:gpt-4o": {"runs": 10, "avg_score": 85.5},
    "copilot:gpt-4": {"runs": 8, "avg_score": 78.3},
    "claude:claude-3.5-sonnet": {"runs": 12, "avg_score": 92.1},
    "claude:claude-3-opus": {"runs": 5, "avg_score": 88.0},
}
```

### Phase 4: Iterative Prompt Optimization (Week 3-4)

#### Step 4.1: Establish Baseline
**Actions**:
1. Run all 4 scenarios with v0.2.0 prompt
2. Test each available agent+model combination
3. Minimum 5 runs per scenario per agent
4. Capture full metrics

**Expected Outcome**: Baseline dashboard showing:
- Which scenarios are hardest
- Which agents perform best
- Common failure patterns

#### Step 4.2: Identify Top Failure Patterns
**Analysis Questions**:
- Do agents stop after N tasks?
- Do they skip status-after-close?
- Do they update during blockers?
- Do they forget about dependencies?
- Do they handle multi-signal scenarios poorly?

**Deliverable**: Ranked list of top 3-5 failure modes

#### Step 4.3: Create Targeted Prompt Improvements
**For Each Failure Pattern**:
1. Add/modify relevant section in handshake prompt
2. Version as v0.3.0, v0.3.1, etc.
3. Test ONLY on scenarios where failure occurs
4. Compare compliance: v0.2.0 vs v0.3.x

**Example**:
```
Failure: Agents stop after 3-4 tasks in full-plan scenario
Fix: Add to prompt:
"Continue autonomously until ALL tasks are DONE. After each update,
check if there are remaining TODO or IN_PROGRESS tasks. If yes,
immediately run status and continue the next task."
```

#### Step 4.4: Regression Testing
**Process**:
1. After each prompt change, rerun ALL scenarios
2. Verify improvement on target scenario
3. Ensure no regression on simpler scenarios
4. Document results in prompt_lab_results.md

### Phase 5: Visualization & Reporting (Week 4+)

#### Dashboard 5.1: Compliance Matrix
```markdown
## Compliance by Scenario & Agent

| Agent+Model | simple | multi-signal | dependency | full-plan | Avg |
|-------------|--------|--------------|------------|-----------|-----|
| copilot:gpt-4o | 95% | 78% | 65% | 42% | 70% |
| copilot:gpt-4 | 88% | 71% | 58% | 35% | 63% |
| claude:3.5-sonnet | 98% | 85% | 72% | 55% | 77% |
| claude:3-opus | 92% | 80% | 68% | 48% | 72% |
```

#### Dashboard 5.2: Failure Analysis
```markdown
## Top Failure Patterns (Last 50 Runs)

1. **Incomplete task execution** (28 occurrences)
   - Most common in: full-plan-completion
   - Worst agents: copilot:gpt-4 (12), openai:gpt-3.5 (10)
   
2. **Missing status-after-close** (18 occurrences)
   - Most common in: multi-signal-cascade
   - Worst agents: claude:3-opus (8), copilot:gpt-4o (7)

3. **Update during blocker** (12 occurrences)
   - Most common in: dependency-chain
   - Worst agents: copilot:gpt-4 (6), openai:gpt-4 (4)
```

## Implementation Checklist

### Week 1: Real Agent Setup ✓ COMPLETE
- [x] Verify Claude CLI available (v2.0.42)
- [x] Verify Copilot CLI available (v0.0.358)
- [x] Test each CLI with simple prompt
- [x] Create copilot_real.sh adapter
- [x] Create claude_real.sh adapter
- [x] Add model detection to adapters
- [x] Run baseline test with real agents
- [x] Create run_iterations.sh for automated testing
- [x] Add performance tracking to README with badges

**Results**: Baseline established at ~26% pass rate, 22/100 avg score

### Week 2: Enhanced Scenarios ⏸️ PAUSED
- [ ] Implement multi-signal-cascade scenario
- [ ] Implement dependency-chain scenario
- [ ] Implement full-plan-completion scenario
- [ ] Add timeout handling (5min max per scenario)
- [ ] Update evaluation to check completion rate
- [ ] Test all scenarios with real agents

**Status**: Focused on prompt optimization first to improve baseline scores

### Week 3: Advanced Metrics ⏳ IN PROGRESS
- [x] Group results by agent+model
- [x] Add model detection from trace logs
- [x] Update aggregate_metrics.py with agent+model tracking
- [x] Update generate_viz.py with model-specific badges
- [ ] Add task completion tracking
- [ ] Add signal handling quality metrics
- [ ] Add workflow quality metrics
- [ ] Create detailed per-run reports

**Status**: Model tracking complete, quality metrics pending

### Week 4: Optimization ⏳ IN PROGRESS
- [x] Run baseline with real agents (53 runs completed)
- [x] Analyze failure patterns (missing updates, status-after, signals)
- [x] Create v0.3.0 prompt with step-by-step improvements
- [x] Test improvements (Copilot: 26.5% → 30.8% pass rate)
- [ ] Continue iterations to reach 50%+ pass rate
- [ ] A/B test different prompt variations
- [ ] Document successful patterns
- [ ] Create harder scenarios when scores reach 60%+

**Current Results** (as of 2025-11-16T21:29Z):
- **Total Runs**: 53
- **Copilot (gpt-5)**: 30.8% pass, 24.5/100 avg score (↑ from 26.5%, 21.7)
- **Claude (sonnet)**: 26.5% pass, 23.5/100 avg score
- **Best Run**: Copilot 70/100 (shows potential with right execution)

**Key Insights**:
- Step-by-step prompts work better than narrative
- Agents need explicit stop conditions
- JSON payload examples help
- Inconsistency suggests need for more examples or simpler tasks

## Success Metrics

**Week 1** ✅ COMPLETE:
- ✅ Testing 2+ real agent CLIs (not mocks) - Copilot & Claude working
- ✅ Model information captured in metrics - Agent+model tracking functional
- ✅ Baseline real-agent compliance scores established - 53 runs, ~26-30% baseline

**Week 2** ⏸️ DEFERRED:
- Scenarios deferred in favor of prompt optimization
- Will implement when baseline scores reach 60%+

**Week 3** ⏳ PARTIAL:
- ✅ Model tracking by agent+model
- ✅ Performance visualization with badges
- ⏳ Advanced quality metrics pending

**Week 4** ⏳ IN PROGRESS:
- ✅ Baseline established and improving (26.5% → 30.8% for Copilot)
- ✅ Prompt v0.3.0 showing measurable gains
- ⏳ Targeting 50%+ pass rate before creating harder scenarios
- ⏳ Documentation of successful patterns ongoing

## Open Questions & Decisions Needed

1. **Time Limits**: Should we kill agents that run >5 minutes? (Leaning YES)
2. **API Keys**: Do real CLIs need auth? (Need to test)
3. **Interactive Prompts**: How to handle agents asking for human input? (Auto-deny?)
4. **Cost Tracking**: Should we monitor API costs if agents use paid APIs?
5. **Parallel Testing**: Run scenarios in parallel or sequential?
6. **Model Selection**: Can we test multiple models per agent automatically?

## Next Immediate Actions

**Continue Prompt Optimization (Week 4)**:
1. Run more iterations: `./labs/run_iterations.sh 10 cli-basics copilot,claude`
2. Target 50%+ pass rate through prompt refinement
3. Document patterns from successful 70/100 runs
4. Consider agent-specific prompts (Claude needs different approach)

**When Scores Reach 60%+**:
1. Create multi-signal-cascade scenario (5 tasks, 3 signals)
2. Test agents on harder workflows
3. Increase difficulty progressively

**Commands**:
```bash
# Continue iterations
cd /Users/honk/code/planloop
./labs/run_iterations.sh 10 cli-basics copilot,claude

# Check current metrics
python labs/aggregate_metrics.py
python labs/generate_viz.py
cat docs/agent-performance.md

# Review successful runs
ls -lt labs/results/ | head -5
cat labs/results/<latest>/copilot/copilot_stdout.txt
```
