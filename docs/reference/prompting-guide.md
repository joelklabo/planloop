# Agent Prompting Guide

**Last Updated:** 2025-11-18  
**Purpose:** Comprehensive guide to effective prompting for planloop agents

---

## Table of Contents

1. [Best Practices by Model](#best-practices-by-model)
2. [Successful Patterns](#successful-patterns)
3. [Agent-Specific Variations](#agent-specific-variations)
4. [Baseline Regression Protection](#baseline-regression-protection)

---

## Best Practices by Model


**Purpose**: Guidelines for crafting effective prompts for different AI agents

**Last Updated**: 2025-11-17

---

## Claude (Anthropic)

### Current Performance
- 39.9% pass rate (improving from 29.3%)
- Avg score: 39.0/100

### Key Strengths
- Deep reasoning, long context
- Methodical/careful approach
- Repo-wide analysis

### Key Weaknesses  
- Can skip steps without explicit structure
- Needs reinforcement and checkpoints

### Optimal Techniques

**1. XML Tags** ⭐ CRITICAL
- Claude processes `<tag>` markup better than plain text
- Use for: rules, workflows, steps, verification, examples
- Impact: +5-10% improvement

**2. Multi-Shot Examples** ⭐ HIGH IMPACT
- Show 2-3 complete workflow examples
- Include exact commands + expected outputs
- Impact: +10-15% improvement

**3. Role Assignment**
- Give specific persona: "meticulous QA automation engineer"
- Emphasize reputation/responsibility
- Impact: +3-5% improvement

**4. Explicit Checkpoints**
- Add `<verification>` after every action
- Aligns with Claude's "human-in-loop" design
- Impact: +5% improvement

**5. Hierarchical Task Breakdown**
- Nest sub-goals under main goals
- Use tree structure vs flat list
- Impact: +5% improvement

**6. Success Criteria Checklist**
- Define "done" with ✓ checkboxes
- Prevents premature stopping
- Impact: +3-5% improvement

### What NOT to Do
❌ Plain markdown without XML  
❌ Vague instructions  
❌ No examples or single example only  
❌ Overly long prompts (>2000 words)

### Research Sources
- Anthropic Prompt Engineering: https://docs.anthropic.com/claude/docs/prompt-engineering
- XML structure (Anthropic recommendation)
- HTNs for procedural tasks (academic research)

---

## GitHub Copilot

### Current Performance
- 46.2% pass rate (v0.0.358 baseline after TTY fix)
- Avg score: 38.5/100
- Previously: 64.3% (authentication working, pre-TTY issue)

### Key Strengths
- IDE-focused, fast completions
- Infers well from context
- Concise and efficient

### Key Weaknesses
- Less deep reasoning
- Prefers brevity over explanation

### Optimal Techniques

**1. Short, Direct Instructions**
- Minimal, focused prompts
- Under 100 lines ideal
- Gets straight to the point

**2. Numbered Lists**
- Clear sequential steps: 1, 2, 3
- Familiar from code comments
- Easy to parse

**3. CRITICAL/MUST Markers**
- Use for emphasis: "CRITICAL:", "MUST"
- Draws attention in brief format
- Works better than paragraphs

**4. Context-Centric**
- Just enough context, no more
- Copilot infers well from minimal input
- Extra text dilutes signal

### What NOT to Do
❌ XML tags (doesn't prioritize them)  
❌ Long examples (confuses model)  
❌ Excessive explanation  
❌ Conversational tone

### Current Status
**v0.3.1 - BASELINE ESTABLISHED**
- Pass rate: 46.2% (post-TTY fix)
- Numbered lists + CRITICAL markers working
- **Next goal: Optimize to 60-70%**

### Version History
- v0.3.1: File-based prompts, TTY fix (46.2% baseline)
- v0.3.0: Added status-after enforcement
- Previous peak: 64.3% (before CLI update issues)

### Research Sources
- GitHub Copilot Docs: https://docs.github.com/en/copilot
- IDE autocomplete patterns (GitHub best practices)

---

## Codex (OpenAI GPT-4)

### Current Performance
- 33.3% pass rate (needs optimization)
- Avg score: 17.9/100

### Key Strengths
- Conversational, versatile
- Balanced reasoning
- Plugin/tool integration

### Key Weaknesses
- Can be too chatty
- Needs clear direction
- May stop prematurely

### Optimal Techniques

**1. Conversational + Directive Mix**
- Blend friendly tone with clear expectations
- "Here's what you need to do..."
- Balance context and command

**2. Goal-Based Framing**
- Start with "why" before "how"
- "Your goal is to..."
- Provides reasoning context

**3. Explicit Success Definition**
- Define "done" clearly upfront
- List concrete criteria
- Prevents partial completion

**4. Iterative Feedback Cues**
- "After each step, verify..."
- Encourages self-checking
- Natural for GPT-4's style

**5. Moderate Structure**
- Markdown headers (## Step 1)
- Lists and bullets
- Not heavy XML (less important)

### What NOT to Do
❌ Too terse (needs some context)  
❌ Heavy XML markup  
❌ Purely imperative (add reasoning)  
❌ Assuming knowledge

### Current Prompt
**v0.1.0** - Conversational + directive hybrid
- Friendly "Let's work together" tone
- Goal framing at top
- Markdown structure with code blocks
- Clear success checklist
- Target: 33% → 50%+

### Research Sources
- OpenAI Prompt Engineering: https://platform.openai.com/docs/guides/prompt-engineering
- GPT-4 technical report (conversational preference)

---

## Universal Patterns (All Agents)

### Always Include
1. Clear objective upfront
2. Step-by-step workflow
3. Verification requirements
4. Success criteria
5. Stop conditions

### Always Avoid
1. Ambiguity
2. Assuming knowledge
3. Missing context (IDs, paths)
4. No examples
5. Overly long (>200 lines)

---

## General Research

### ReAct Pattern
- Thought → Action → Observation loops
- Explicit reasoning checkpoints
- https://arxiv.org/abs/2210.03629

### Procedural Knowledge for Agents
- HTNs reduce step-skipping
- Hierarchical goals > flat lists
- https://arxiv.org/abs/2511.07568

### Step-Level Guidance
- Feedback at each stage improves reliability
- Checkpoints enforce compliance
- Multiple papers support this

---

## Automated Prompt Optimization

### DSPy Framework

**What It Is**: Framework for programmatically optimizing prompts using ML
- URL: https://github.com/stanfordnlp/dspy
- Optimizers: MIPRO, BootstrapFewShot, etc.
- Requires: Training examples with inputs/outputs

**When to Use**:
- Complex multi-step workflows
- Large training datasets available (20+ examples)
- Need data-driven optimization vs manual iteration
- Have compute budget for optimization runs

**When NOT to Use**:
- Simple, well-understood tasks
- Limited training examples (<10)
- Constrained by cost (optimization uses many API calls)
- Prompts already working well (>70% success)

**Our Experience**:
- ❌ DSPy struggled with our workflow (planloop compliance)
- Issue: Signature was too abstract for optimizer
- Better: Manual iteration with targeted fixes based on failure analysis
- Lesson: DSPy works better for knowledge tasks than procedural workflows

**Alternative Approaches**:
- Manual prompt engineering with A/B testing (what we're doing)
- Failure pattern analysis → targeted fixes
- Small iterative improvements (5-10% gains)
- Regular baseline testing to prevent regression

---

## Maintenance

**When to Update**:
- After discovering new techniques
- When performance plateaus
- After agent model updates
- When research reveals new patterns

**Version History**:
- v1.1 (2025-11-17): Added DSPy learnings, Copilot TTY fix
- v1.0 (2025-11-17): Initial guide based on 218 test runs + research

---

## Successful Patterns


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

---

## Agent-Specific Variations


## Overview

Each agent (Copilot, Claude, OpenAI) has its own optimized prompt file tailored to its specific strengths and weaknesses. This allows independent iteration on prompts without affecting other agents.

## Structure

All agent prompts are stored in `labs/prompts/` with a consistent naming convention:

```
labs/prompts/
├── copilot-v0.3.1.txt    # GitHub Copilot prompt
├── claude-v0.3.2.txt     # Anthropic Claude prompt
└── openai-v0.1.txt       # OpenAI prompt
```

### Naming Convention

`<agent>-v<major>.<minor>.txt`

- **agent**: lowercase agent name (copilot, claude, openai)
- **version**: semver-style versioning
  - Major: significant structural changes
  - Minor: incremental improvements

## Agent Adapter Scripts

Each agent has an adapter script in `labs/agents/` that loads the appropriate prompt:

```bash
# labs/agents/copilot_real.sh
PROMPT_FILE="$SCRIPT_DIR/../prompts/copilot-v0.3.1.txt"
if [ -n "${PLANLOOP_LAB_AGENT_PROMPT:-}" ]; then
  prompt="$PLANLOOP_LAB_AGENT_PROMPT"
elif [ -f "$PROMPT_FILE" ]; then
  prompt=$(sed "s/\$SESSION/$session/g" "$PROMPT_FILE")
else
  echo "Error: Prompt file not found: $PROMPT_FILE"
  exit 1
fi
```

### Environment Variable Override

All agents support `PLANLOOP_LAB_AGENT_PROMPT` for testing custom prompts:

```bash
export PLANLOOP_LAB_AGENT_PROMPT="Your custom prompt here"
python labs/run_lab.py --scenario cli-basics --agents copilot
```

## Current Prompts

### Copilot (v0.3.1)

**File**: `labs/prompts/copilot-v0.3.1.txt`  
**Performance**: 58.3% pass rate, 44.8/100 avg score  
**Key Patterns**:
- ALL CAPS CRITICAL rules at top
- Numbered workflow steps with exact commands
- Inline (CRITICAL: ...) comments
- Response format specification

**Optimized for**: Brief, structured, code-like instructions

### Claude (v0.3.2)

**File**: `labs/prompts/claude-v0.3.2.txt`  
**Performance**: 46.2% pass rate, 41.7/100 avg score  
**Key Patterns**:
- Simplified structure (14 lines vs 47 in v0.3.1)
- **BOLD** emphasis for critical rules
- High-level workflow (not overly detailed)
- Clear goal statement

**Optimized for**: Concise, high-level guidance with room for reasoning

### OpenAI (v0.1.0)

**File**: `labs/prompts/openai-v0.1.txt`  
**Performance**: 5.3% pass rate, 3.5/100 avg score  
**Status**: Needs significant work, deprioritized

**Key Patterns**:
- Conversational + directive hybrid
- Goal-based framing
- Markdown structure

**Optimized for**: (To be determined after more testing)

## Versioning and Baseline Tracking

All prompt versions are tracked in `labs/baseline.json`:

```json
{
  "copilot": {
    "pass_rate": 58.3,
    "avg_score": 44.8,
    "version": "v0.3.1",
    "prompt_file": "labs/prompts/copilot-v0.3.1.txt",
    "last_updated": "2025-11-17"
  }
}
```

## Workflow for Updating Prompts

### 1. Create New Prompt Version

```bash
# Copy current version
cp labs/prompts/copilot-v0.3.1.txt labs/prompts/copilot-v0.3.2.txt

# Edit the new version
vim labs/prompts/copilot-v0.3.2.txt
```

### 2. Update Agent Adapter

```bash
# Edit labs/agents/copilot_real.sh
# Change: PROMPT_FILE="$SCRIPT_DIR/../prompts/copilot-v0.3.2.txt"
```

### 3. Test Changes

```bash
# Run iterations
./labs/run_iterations.sh 30 cli-basics copilot

# Check for regressions
./labs/check_baseline.sh
```

### 4. Update Baseline if Improved

```bash
# Auto-detect and update
./labs/update_baseline.sh copilot --auto-detect

# Review changes
git diff labs/baseline.json
```

### 5. Commit Together

```bash
git add labs/prompts/copilot-v0.3.2.txt \
        labs/agents/copilot_real.sh \
        labs/baseline.json

git commit -m "Optimize Copilot prompt to v0.3.2

- Improved status-after emphasis
- Pass rate: 58.3% → 62.1%
- Updated baseline configuration"
```

## Benefits of Agent-Specific Prompts

### 1. Independent Optimization

Each agent can be optimized without affecting others:
- Copilot's brief style doesn't constrain Claude's detailed approach
- Claude's simplification doesn't force Copilot to lose structure

### 2. Regression Protection

`labs/check_baseline.sh` ensures Copilot doesn't regress when optimizing Claude:
```bash
=== Checking Copilot Baseline ===
Baseline: 58.3% pass rate
Current:  58.1% pass rate
✅ No significant regression detected
```

### 3. A/B Testing

Easy to test variations:
```bash
# Test variation A
export PLANLOOP_LAB_AGENT_PROMPT="$(cat prompts/copilot-v0.3.2-variant-a.txt)"
./labs/run_iterations.sh 10 cli-basics copilot

# Test variation B
export PLANLOOP_LAB_AGENT_PROMPT="$(cat prompts/copilot-v0.3.2-variant-b.txt)"
./labs/run_iterations.sh 10 cli-basics copilot
```

### 4. Version Control

All prompt changes tracked in git:
- See what changed: `git diff copilot-v0.3.1.txt copilot-v0.3.2.txt`
- Revert if needed: `git checkout HEAD~1 -- labs/prompts/copilot-v0.3.2.txt`
- Blame for history: `git blame labs/prompts/copilot-v0.3.1.txt`

## Design Patterns Across Agents

While each agent has unique prompts, successful patterns include:

### Universal Elements

1. **Status-After Emphasis**: All agents need explicit "run status after update" instruction
2. **Stop Conditions**: Clear definition of completion ("until all tasks are DONE")
3. **Session Variable**: Use `$SESSION` placeholder (replaced by adapter)
4. **PLANLOOP_LAB_AGENT_PROMPT**: Environment variable override for testing

### Agent-Specific Adaptations

| Pattern | Copilot | Claude | OpenAI |
|---------|---------|--------|--------|
| Formatting | ALL CAPS + numbered | **Bold** + numbered | Markdown headers |
| Detail Level | Exact commands | High-level steps | Moderate detail |
| Length | 35 lines | 14 lines | 15 lines |
| Tone | Imperative | Directive | Conversational |

## Testing

Test suite: `tests/test_agent_prompts.py`

**Validates**:
- ✅ Each agent has versioned prompt file
- ✅ Prompts are non-empty and reference planloop
- ✅ Agent scripts load from files (not hardcoded)
- ✅ Prompt versions tracked in baseline.json

Run tests:
```bash
pytest tests/test_agent_prompts.py -v
```

## Future Work

### Short Term

1. **Copilot**: Reach 60%+ baseline (currently 58.3%)
2. **Claude**: Optimize to 60%+ (currently 46.2%)
3. **OpenAI**: Investigate trace logging issue (currently 5.3%)

### Long Term

1. **Automated A/B Testing**: Compare prompt variations statistically
2. **Prompt Libraries**: Maintain multiple prompts per agent for different scenarios
3. **Cross-Agent Patterns**: Extract universally successful techniques
4. **Dynamic Prompts**: Generate agent-specific prompts programmatically

## See Also

- `docs/reference/successful-prompt-patterns.md` - Detailed pattern analysis
- `docs/reference/baseline-regression-protection.md` - Regression protection system
- `docs/lab-testing.md` - Testing infrastructure
- `labs/baseline.json` - Current baseline configuration

---

## Baseline Regression Protection


## Overview

The regression protection system prevents unintentional performance degradation when optimizing agent prompts. It tracks baseline performance for each agent and alerts when changes cause significant regressions.

## Components

### 1. Baseline Configuration (`labs/baseline.json`)

Version-controlled JSON file tracking baseline performance for each agent:

```json
{
  "copilot": {
    "pass_rate": 58.3,
    "avg_score": 44.8,
    "version": "v0.3.1",
    "last_updated": "2025-11-17",
    "prompt_file": "labs/prompts/copilot-v0.3.1.txt",
    "notes": "Baseline established after environment setup improvements"
  },
  "config": {
    "regression_threshold": 5.0,
    "description": "Maximum acceptable drop in pass rate before alerting"
  }
}
```

### 2. Baseline Checker (`labs/check_baseline.sh`)

Compares current Copilot performance against baseline:

```bash
./labs/check_baseline.sh
```

**Exit codes**:
- `0`: No regression detected
- `1`: Significant regression detected (>5% drop in pass rate)

**Output**:
```
=== Checking Copilot Baseline ===
Baseline: 58.3% pass rate, 44.8 avg score
Current:  60.2% pass rate, 46.0 avg score

✅ No significant regression detected ↑
```

### 3. Baseline Updater (`labs/update_baseline.sh`)

Updates baseline values when improvements are made:

```bash
# Auto-detect current performance
./labs/update_baseline.sh copilot --auto-detect

# Manual entry
./labs/update_baseline.sh copilot
```

**Workflow**:
1. Detects current performance from `labs/metrics.json`
2. Prompts for confirmation
3. Requests prompt version and notes
4. Updates `labs/baseline.json`
5. Reminds to commit the changes

### 4. CI Integration

GitHub Actions workflow automatically checks for regressions when:
- Commit messages contain "prompt" or "Optimize"
- Files in `labs/prompts/` or `labs/agents/` are modified
- `labs/baseline.json` is modified

**CI Job**: `baseline-regression-check`

If regression detected:
```
⚠️  Baseline regression detected!
If this is intentional, update the baseline:
  ./labs/update_baseline.sh copilot --auto-detect

Include the updated labs/baseline.json in your commit.
```

## Workflow

### Optimizing Agent Prompts

1. **Before optimization**: Check current baseline
   ```bash
   ./labs/check_baseline.sh
   ```

2. **Make prompt changes**: Edit prompt files in `labs/prompts/` or `labs/agents/`

3. **Test changes**: Run iterations
   ```bash
   ./labs/run_iterations.sh 30 cli-basics claude
   ```

4. **Check for regression**: After optimization
   ```bash
   ./labs/check_baseline.sh
   ```

5. **If Copilot improved**: Update baseline
   ```bash
   ./labs/update_baseline.sh copilot --auto-detect
   git add labs/baseline.json
   ```

6. **Commit**: Include baseline updates with prompt changes
   ```bash
   git commit -m "Optimize Claude prompt to 55%
   
   - Updated Claude prompt structure
   - Pass rate improved from 46% to 55%
   - Updated Copilot baseline to 60.2% (no regression)"
   ```

### Using optimize_safely.sh

The safe optimization script automates this workflow:

```bash
./labs/optimize_safely.sh claude 30
```

**Steps**:
1. Checks Copilot baseline
2. Snapshots current metrics
3. Runs optimization iterations
4. Checks for regression
5. Reports results or alerts on regression

## Configuration

### Regression Threshold

Default: 5.0% (pass rate drop)

To change, edit `labs/baseline.json`:
```json
{
  "config": {
    "regression_threshold": 3.0
  }
}
```

### Tracked Agents

Currently tracking:
- **Copilot** (primary - regression protection enforced)
- **Claude** (secondary - for reference)
- **OpenAI** (tertiary - for reference)

## Design Rationale

### Why Copilot-Focused?

Copilot has the highest baseline performance (58.3%) and is the primary target. When optimizing Claude or OpenAI, we must ensure Copilot doesn't regress.

### Why Version-Controlled Baseline?

1. **Transparency**: All baseline changes are tracked in git history
2. **Reproducibility**: Any commit can be checked against its baseline
3. **Accountability**: Baseline updates require explicit commits
4. **Documentation**: Git log shows why baselines changed

### Why 5% Threshold?

- Small enough to catch meaningful regressions
- Large enough to avoid false positives from variance
- Based on statistical analysis of 700+ test runs

## Troubleshooting

### False Positive: "Regression detected" but performance is stable

**Cause**: Baseline may be outdated  
**Solution**: Update baseline if current performance is consistently higher
```bash
./labs/update_baseline.sh copilot --auto-detect
```

### CI failing on baseline check

**Cause**: Prompt changes affected Copilot negatively  
**Solutions**:
1. **Revert prompt changes** if unintentional
2. **Use agent-specific prompts** if necessary
3. **Update baseline** if regression is acceptable trade-off

### Baseline updater can't find metrics

**Cause**: `labs/metrics.json` doesn't have recent data  
**Solution**: Run lab tests first
```bash
./labs/run_iterations.sh 10 cli-basics copilot
python3 labs/aggregate_metrics.py
```

## Testing

Test suite: `tests/test_regression_protection.py`

**Coverage**:
- ✅ Baseline config file exists
- ✅ Config has proper structure
- ✅ Values are reasonable (0-100 ranges)
- ✅ check_baseline.sh reads from JSON
- ✅ CI workflow includes regression check
- ✅ Update script exists and is executable

Run tests:
```bash
pytest tests/test_regression_protection.py -v
```

## Future Enhancements

1. **Multi-Agent Protection**: Extend to Claude and OpenAI once they reach 60%+
2. **Automated Rollback**: Auto-revert commits that cause regressions
3. **Performance Tracking**: Long-term trend analysis
4. **Baseline Recommendations**: Suggest when to update baselines
5. **A/B Testing Integration**: Compare prompt variations safely

## See Also

- `docs/reference/successful-prompt-patterns.md` - Documented prompt patterns
- `docs/lab-testing.md` - Lab testing infrastructure
- `docs/agent-performance.md` - Current agent metrics
- `labs/optimize_safely.sh` - Safe optimization workflow
