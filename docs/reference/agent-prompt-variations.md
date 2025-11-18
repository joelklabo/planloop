# Agent-Specific Prompt Variations

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
