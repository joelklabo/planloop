# Successful Prompt Patterns for Planloop Agents

**Purpose**: Document the actual prompts and patterns that achieved measurable performance improvements in agent compliance testing.

**Last Updated**: 2025-11-17  
**Status**: Based on 722+ test runs across Copilot, Claude, and OpenAI

---

## Performance Summary

| Agent | Pass Rate | Avg Score | Prompt Version | Status |
|-------|-----------|-----------|----------------|--------|
| **Copilot (gpt-5)** | 58.3% | 44.8/100 | v0.3.1 | ✅ Baseline achieved |
| **Claude (sonnet)** | 46.2% | 41.7/100 | v0.3.2 | 🔄 Optimizing toward 60% |
| **OpenAI** | 5.3% | 3.5/100 | v0.1.0 | ⏳ Needs work |

**Target**: 60%+ pass rate for all agents

---

## GitHub Copilot (v0.3.1)

### Performance
- **Current**: 58.3% pass rate, 44.8/100 avg score
- **Previous Peak**: 64.3% (before CLI update issues)
- **Improvement**: +12.1% from initial baseline

### Successful Patterns

#### 1. **CRITICAL Rules at Top** ⭐ HIGH IMPACT
Start with numbered CRITICAL RULES in ALL CAPS:
```markdown
**CRITICAL RULES:**
1.  **ALWAYS** run 'planloop status' after *every* action
2.  **NEVER** stop until all tasks are 'completed'
```

**Why it works**: Copilot prioritizes brief, emphatic directives. ALL CAPS + numbered format = maximum attention.

**Impact**: +8% improvement over conversational prompts

#### 2. **Response Format Specification**
Explicitly define output structure:
```markdown
**RESPONSE FORMAT:**
You must respond with a "Thought" section followed by commands.

Thought: <Your reasoning>

<COMMANDS TO EXECUTE>
```

**Why it works**: Copilot needs clear structure for code-like outputs. Reduces ambiguity.

**Impact**: +5% improvement in command execution accuracy

#### 3. **Numbered Workflow Steps with Exact Commands**
Provide step-by-step workflow with copy-paste commands:
```markdown
**WORKFLOW STEPS:**

1.  **GET STATUS:**
    `planloop status --session $SESSION --json`

2.  **HANDLE BLOCKERS:**
    `planloop alert --close --id <signal-id>`
    `planloop status --session $SESSION --json` (CRITICAL: Verify)
```

**Why it works**: Copilot excels at following structured, code-like instructions. Exact commands reduce interpretation errors.

**Impact**: +6% improvement in workflow adherence

#### 4. **Inline CRITICAL Comments**
Add (CRITICAL: ...) after important steps:
```markdown
`planloop status --session $SESSION --json` (CRITICAL: Verify update)
```

**Why it works**: Mirrors code comment style. Familiar to Copilot's training data.

**Impact**: +3% reduction in missing verification steps

### Full Prompt (v0.3.1)
```markdown
**CRITICAL RULES:**
1.  **ALWAYS** run 'planloop status --session $SESSION --json' after *every* action that modifies the plan or session state.
2.  **NEVER** stop until 'planloop status --session $SESSION --json' shows all tasks are 'completed'.

You are an AI agent interacting with the 'planloop' CLI. Your goal is to complete ALL tasks and handle ALL blockers within a given session.

**RESPONSE FORMAT:**
You must respond with a "Thought" section followed by the commands to execute.

Thought: <Your reasoning process here, explaining what you are doing and why.>

<COMMANDS TO EXECUTE>

**WORKFLOW STEPS (Generate and execute these commands):**

1.  **GET STATUS:**
    `planloop status --session $SESSION --json`

2.  **HANDLE BLOCKERS (if 'now.reason' is 'ci_blocker' or 'lint_blocker'):**
    `planloop alert --close --id <signal-id>` (replace <signal-id> with 'now.blocker_id')
    `planloop status --session $SESSION --json` (CRITICAL: Verify blocker cleared)

3.  **HANDLE TASKS (if 'now.reason' is 'task'):**
    a.  **MARK IN_PROGRESS:**
        `echo '{"tasks": [{"id": "<task-id>", "status": "IN_PROGRESS"}]}' > payload.json` (replace <task-id> with 'now.task_id')
        `planloop update --session $SESSION --file payload.json`
        `planloop status --session $SESSION --json` (CRITICAL: Verify update)
    b.  **MARK DONE:**
        `echo '{"tasks": [{"id": "<task-id>", "status": "DONE"}]}' > payload.json` (replace <task-id> with 'now.task_id')
        `planloop update --session $SESSION --file payload.json`
        `planloop status --session $SESSION --json` (CRITICAL: Verify update)

**IMPORTANT:**
-   Prioritize running `planloop status` to get the latest state.
-   Ensure all tasks are marked 'DONE' before stopping.
```

**Location**: `labs/prompts/copilot-v0.3.1.txt`

### What NOT to Do with Copilot
❌ XML tags (doesn't prioritize them like Claude)  
❌ Long explanations (dilutes signal)  
❌ Conversational tone (too verbose)  
❌ Overly nested structure (keep flat)

### Version History
- **v0.3.1** (Current): File-based prompts, TTY fix, 58.3% pass rate
- **v0.3.0**: Added status-after enforcement, ~55% pass rate
- **v0.2.x**: Initial numbered lists approach, ~48% pass rate

### Top Remaining Failures
1. **Missing status-after** (29.9% of failures) - Still needs work
2. **Missing update** (34.1% of failures) - Command not executed
3. **Premature stopping** (15.2% of failures) - Stops before all tasks done

---

## Claude (v0.3.2)

### Performance
- **Current**: 46.2% pass rate, 41.7/100 avg score
- **Previous**: 37.8% pass rate (v0.3.1)
- **Improvement**: +8.4% from prompt simplification

### Successful Patterns

#### 1. **Simplified Structure** ⭐ HIGH IMPACT
**BEFORE (v0.3.1)**: 47 lines, nested sections, heavy formatting
**AFTER (v0.3.2)**: 14 lines, flat structure, minimal formatting

```markdown
You are an AI agent designed to interact with the 'planloop' CLI tool. 
Your primary goal is to complete all assigned tasks and resolve any blockers.

**CRITICAL RULE: ALWAYS RUN 'planloop status' AFTER EVERY ACTION**
This includes after 'planloop update' and 'planloop alert --close'.
```

**Why it works**: Claude was getting lost in complex structure. Simplification improved focus.

**Impact**: +8.4% improvement (37.8% → 46.2%)

#### 2. **Bold Emphasis for Critical Rules**
Use **BOLD** for must-do actions:
```markdown
**CRITICAL RULE: ALWAYS RUN 'planloop status' AFTER EVERY ACTION**
```

**Why it works**: Visual emphasis helps Claude prioritize. Less effective than Copilot's ALL CAPS but still works.

**Impact**: +4% reduction in missing status-after

#### 3. **Numbered Workflow (High-Level Only)**
Keep workflow high-level, not overly detailed:
```markdown
**WORKFLOW:**
1.  **Start/Loop:** Run 'planloop status --session $session --json'
2.  **Handle Blockers:** Close signal, then run status
3.  **Handle Tasks:** Mark IN_PROGRESS, then DONE, run status after each
4.  **Completion:** Continue until all tasks completed
```

**Why it works**: Claude can fill in details. Over-specification causes confusion.

**Impact**: +3% improvement in workflow adherence

#### 4. **Explicit Goal Statement**
State primary goal upfront:
```markdown
Your primary goal is to complete all assigned tasks and resolve any blockers.
```

**Why it works**: Claude benefits from clear objective framing. Prevents premature stopping.

**Impact**: +2% reduction in incomplete runs

### Full Prompt (v0.3.2)
```markdown
You are an AI agent designed to interact with the 'planloop' CLI tool. Your primary goal is to complete all assigned tasks and resolve any blockers within a given session.

**CRITICAL RULE: ALWAYS RUN 'planloop status' AFTER EVERY ACTION THAT MODIFIES THE PLAN OR SESSION STATE.**
This includes after 'planloop update' and 'planloop alert --close'.

**WORKFLOW:**
1.  **Start/Loop:** Begin by running 'planloop status --session $session --json' to understand the current state.
2.  **Handle Blockers:** If 'now.reason' indicates a 'ci_blocker' or 'lint_blocker', close the signal using 'planloop alert --close --id <signal-id>' (from 'now.blocker_id'), then immediately run 'planloop status --session $session --json'.
3.  **Handle Tasks:** If 'now.reason' is 'task', mark the task 'IN_PROGRESS' and then 'DONE' using 'planloop update --session $session --file payload.json'. Remember to run 'planloop status --session $session --json' after each 'planloop update'.
4.  **Completion:** Continue this loop until 'planloop status' shows all tasks are completed ('now.reason' is 'completed').

**IMPORTANT:**
- Always prioritize running 'planloop status' to get the latest state.
- Ensure all tasks are marked 'DONE' before stopping.
- Do not stop if tasks are still 'TODO' or 'IN_PROGRESS'.
```

**Location**: Embedded in `labs/agents/claude_real.sh` (lines 19-34)

### What NOT to Do with Claude
❌ Overly complex structure (causes confusion)  
❌ Too much detail (Claude over-thinks)  
❌ Flat imperative style (needs some reasoning context)  
❌ Missing explicit stop conditions (stops early)

### Version History
- **v0.3.2** (Current): Simplified prompt, 46.2% pass rate
- **v0.3.1**: Complex multi-section format, 37.8% pass rate
- **v0.3.0**: Initial XML-heavy approach, ~35% pass rate

### Top Remaining Failures
1. **Missing status-after** (47.1% of failures) - Most critical issue
2. **Missing update** (45.7% of failures) - Second most critical
3. **Signal not closed** (3.9% of failures) - Minor issue

### Next Optimization Targets
To reach 60% pass rate, need to address:
1. Strengthen "status-after" requirement (add more emphasis)
2. Make update command more explicit (show exact JSON format)
3. Add verification checkpoints (force self-checking)

---

## OpenAI (v0.1.0)

### Performance
- **Current**: 5.3% pass rate, 3.5/100 avg score
- **Status**: ⏳ Needs significant work
- **Issue**: Most runs produce no trace log (76% of failures)

### Current Approach (v0.1.0)
Conversational + directive hybrid:
```markdown
You are collaborating with 'planloop' CLI to manage tasks and signals.

**Your Mission:** Complete all tasks, resolve all blockers, stop when done.

**CRITICAL: After EVERY 'planloop update' or 'planloop alert', run 'planloop status'**

[... workflow steps ...]
```

**Location**: `labs/prompts/openai-v0.1.txt`

### Known Issues
1. **Trace log missing** (76% of failures) - Agent not executing commands properly
2. **Missing status-after** (18.6% of failures)
3. **Missing update** (17.1% of failures)

### Status
**Deprioritized** - Focusing on Copilot and Claude optimization first.  
Target: Re-evaluate after Copilot and Claude reach 60%+ baseline.

---

## Universal Patterns (All Agents)

### Successful Techniques Across All Agents

1. **Status-After Emphasis** ⭐ CRITICAL
   - Every agent needs explicit "run status after update" instruction
   - Use agent-appropriate emphasis (ALL CAPS for Copilot, BOLD for Claude)
   - Repeat this rule multiple times if needed
   - **Impact**: Single biggest predictor of success

2. **Explicit Stop Conditions**
   - Always specify when to stop: "until 'now.reason' is 'completed'"
   - Prevents premature stopping
   - **Impact**: +5-8% improvement across all agents

3. **Concrete Examples**
   - Show exact commands with placeholders: `<task-id>`
   - Reduces interpretation errors
   - **Impact**: +3-5% improvement

4. **Session Variable Substitution**
   - Use `$SESSION` or `$session` in prompts
   - Gets replaced with actual session ID by adapter scripts
   - Critical for multi-session testing

### What NOT to Do (Universal)
❌ Assume agents remember context (they don't)  
❌ Use vague language ("handle appropriately")  
❌ Omit session ID in commands  
❌ Mix multiple formatting styles (confuses all agents)  
❌ Skip verification steps  

---

## Optimization Methodology

### How We Discovered These Patterns

1. **Baseline Measurement**
   - Run 20+ iterations of `cli-basics` scenario
   - Measure pass rate and avg score
   - Identify top 3 failure patterns

2. **Failure Analysis**
   - Review `labs/results/<run-id>/` outputs
   - Look for common patterns in failures
   - Categorize by type (missing status-after, missing update, etc.)

3. **Targeted Iteration**
   - Change ONE thing in prompt
   - Run 10+ iterations to measure impact
   - Compare to baseline with `labs/check_baseline.sh`
   - Keep if improves performance, revert if regresses

4. **Pattern Extraction**
   - Document what worked
   - Extract general principles
   - Test across different agents

5. **Continuous Validation**
   - Regular regression testing with `labs/run_iterations.sh`
   - Update `docs/agent-performance.md` with metrics
   - Track long-term trends

### Tools
- `labs/run_lab.py` - Single test run
- `labs/run_iterations.sh` - Batch testing
- `labs/check_baseline.sh` - Regression detection
- `labs/optimize_safely.sh` - Safe optimization workflow
- `labs/aggregate_metrics.py` - Performance analysis
- `labs/generate_viz.py` - Visualization generation

### Metrics Tracked
- **Pass rate**: % of runs with 100% compliance
- **Avg score**: 0-100 scale of workflow compliance
- **Top errors**: Most common failure patterns
- **Model version**: Which specific model was used

---

## Research Sources

### Academic & Industry Research
1. **ReAct Pattern** (arXiv:2210.03629)
   - Thought → Action → Observation loops
   - Explicit reasoning checkpoints
   - Applied in our "Thought" section requirement

2. **Procedural HTNs** (arXiv:2511.07568)
   - Hierarchical task networks reduce step-skipping
   - Inspired our nested workflow structure (though Claude needs flat)

3. **Anthropic Prompt Engineering**
   - https://docs.anthropic.com/claude/docs/prompt-engineering
   - XML structure recommendations (mixed results for us)
   - Checkpoint pattern (high impact)

4. **GitHub Copilot Best Practices**
   - https://docs.github.com/en/copilot
   - Code-comment style directives
   - Brief, structured format

5. **OpenAI Prompt Engineering**
   - https://platform.openai.com/docs/guides/prompt-engineering
   - Conversational + directive balance
   - Goal-based framing

### Automated Optimization Attempts

#### DSPy Framework
- **Tried**: MIPRO optimizer for prompt optimization
- **Result**: ❌ Failed to improve performance
- **Reason**: Our task is procedural workflow, not knowledge retrieval
- **Lesson**: Manual iteration with failure analysis works better for procedural tasks
- **See**: `docs/reference/prompt-optimization.md` for detailed DSPy analysis

---

## Future Work

### To Reach 60% for All Agents

**Copilot** (58.3% → 60%+):
- Strengthen status-after emphasis (add more CRITICAL markers)
- Add verification checklist at end
- Consider inline examples in workflow steps

**Claude** (46.2% → 60%+):
- Test XML-tagged version of v0.3.2
- Add explicit checkpoints after each action
- Strengthen stop conditions

**OpenAI** (5.3% → 60%+):
- Fix trace logging issue first (root cause)
- Try Copilot-style format (might work better than conversational)
- Consider switching to different OpenAI CLI tool

### Advanced Scenarios (After 60% Baseline)
Once all agents hit 60%+ on `cli-basics`:
1. `multi-signal-cascade` - 5 tasks, 3 signals at different stages
2. `dependency-chain` - Complex task dependencies
3. `full-plan-completion` - Realistic 12-task feature implementation

### Long-Term Research
- Agent-specific prompt libraries
- Automated regression testing on every commit
- Prompt versioning and A/B testing framework
- Cross-agent pattern transfer learning

---

## Maintenance

**When to Update**:
- After any prompt optimization that changes pass rate
- When agent CLIs are updated (may break compatibility)
- When new failure patterns emerge
- After reaching performance milestones (60%, 70%, 80%)

**Version Tracking**:
- Prompt versions: `labs/prompts/<agent>-v<X>.<Y>.txt`
- Performance data: `docs/agent-performance.md`
- This document: Update history section below

**Update History**:
- **v1.0** (2025-11-17): Initial documentation based on 722 test runs
  - Copilot v0.3.1: 58.3% pass rate
  - Claude v0.3.2: 46.2% pass rate
  - OpenAI v0.1.0: 5.3% pass rate
