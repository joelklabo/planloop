# Successful Prompt Patterns for AI Agents

This document captures successful patterns discovered through automated testing of AI agents with planloop. Each pattern is validated through real agent runs and measurable performance improvements.

## Overview

Agent testing with planloop revealed that different AI models respond better to different prompt patterns. This document consolidates successful patterns by agent type, including:

- **Performance metrics** - Pass rates and quality scores
- **Prompt versions** - Specific prompt content that worked
- **What worked** - Patterns that improved agent performance
- **What didn't work** - Approaches that failed or underperformed

**Last Updated**: 2025-11-18  
**Test Framework**: labs/run_lab.py with automated compliance tracking

---

## GitHub Copilot Patterns

### Performance Summary

**Current Performance** (v0.3.1, 158 runs as of 2025-11-17):
- **Pass Rate**: 64.3%
- **Status**: ✅ Target achieved (60%+ baseline)
- **Model**: gpt-5 (GitHub Copilot CLI)

### Successful Patterns

**1. Explicit Next Actions**
- ✅ **Pattern**: Include `next_action` field in status JSON with explicit guidance
- ✅ **Why it works**: Copilot excels at following structured guidance
- ✅ **Example**: 
  ```json
  {
    "next_action": {
      "action": "continue",
      "task_id": 2,
      "message": "Continue with next task 2: [title]"
    }
  }
  ```

**2. TDD Workflow Enforcement**
- ✅ **Pattern**: Include TDD checklist in every status response
- ✅ **Why it works**: Copilot responds well to step-by-step processes
- ✅ **Implementation**: See `_get_tdd_checklist()` in cli.py

**3. Transition Detection**
- ✅ **Pattern**: Explicitly signal when tasks complete via `transition_detected` field
- ✅ **Why it works**: Copilot can autonomously continue when it knows a task finished
- ✅ **Result**: Reduced "what should I do next?" stopping points by 80%+

### Prompt Version: v0.3.1

Key characteristics:
- Autonomous continuation loop emphasized
- TDD workflow made prominent with checklist
- next_action guidance in every status response
- Transition detection for seamless task chaining
- Examples showing continuous work without stopping

**Location**: `labs/prompts/copilot-v0.3.1.txt`

### What Didn't Work

- ❌ Generic instructions without structure (v0.1 pass rate: ~40%)
- ❌ Assuming agent knows to check status after completing tasks
- ❌ Vague "continue working" without specific next task ID

---

## Claude Patterns

### Performance Summary

**Current Performance** (v0.3.2, 158 runs as of 2025-11-17):
- **Pass Rate**: 46.2%
- **Status**: ⏳ Needs improvement (+13.8% to reach 60% target)
- **Model**: claude-3-5-sonnet-20241022

### Successful Patterns

**1. Workflow Contract Emphasis**
- ✅ **Pattern**: Start with explicit workflow rules before any instructions
- ✅ **Why it works**: Claude responds well to formal contracts and rules
- ✅ **Example**: "## Workflow contract" section first, before command reference

**2. Autonomous Loop Examples**
- ✅ **Pattern**: Concrete examples showing full task-to-task flow
- ✅ **Why it works**: Claude learns better from examples than abstract descriptions
- ✅ **Implementation**: "Autonomous Loop Example" section with bash script

**3. Non-Negotiable TDD**
- ✅ **Pattern**: Frame TDD as "NON-NEGOTIABLE" with checklist
- ✅ **Why it works**: Claude respects explicit constraints
- ✅ **Result**: Improved test coverage in agent runs

### Prompt Version: v0.3.2

Key characteristics:
- Workflow contract prominently positioned
- Autonomous continuation loop with concrete examples
- TDD emphasized as non-negotiable
- Command reference includes status → update → status pattern
- Examples show working without stopping

**Location**: `labs/prompts/claude-v0.3.2.txt`

### What Didn't Work

- ❌ Buried workflow rules in middle of document
- ❌ Assuming Claude would infer autonomous behavior
- ❌ Generic "keep working" without demonstrating HOW

### Improvement Opportunities

**Current gaps** (based on 46.2% pass rate):
1. Claude still stops to ask "what next?" even with next_action
2. May need more explicit "NEVER stop to ask" language
3. Could benefit from negative examples ("❌ DON'T do this")

---

## OpenAI Patterns

### Performance Summary

**Current Performance** (v0.1, 158 runs as of 2025-11-17):
- **Pass Rate**: 5.7%
- **Status**: ⏳ Significant improvement needed (+54.3% to reach target)
- **Model**: gpt-4-turbo
- **Note**: Deprioritized for optimization (Phase 3)

### Prompt Version: v0.1

**Location**: `labs/prompts/openai-v0.1.txt`

### Known Issues

- Very low pass rate suggests fundamental prompt structure issues
- May need complete rework rather than incremental optimization
- Currently deprioritized pending Copilot/Claude success

---

## Cross-Agent Patterns

### Universal Success Patterns

**1. Explicit Status → Action Flow**
- All agents benefit from structured status responses
- next_action field universally helpful
- JSON schema clarity critical

**2. TDD Workflow Visibility**
- Making TDD steps visible in status improves compliance
- Checklist format works across agents
- "Test first" pattern reduces quality issues

**3. Transition Detection**
- Detecting task completion enables autonomous continuation
- Works well for Copilot, partial success with Claude
- Key to preventing "stopping to ask" behavior

### Agent-Specific Optimizations

| Pattern | Copilot | Claude | OpenAI |
|---------|---------|--------|--------|
| Explicit next_action | ✅ Excellent | ⚠️ Moderate | ❌ Poor |
| TDD checklist | ✅ Excellent | ✅ Good | ❓ Unknown |
| Workflow contract | ✅ Good | ✅ Excellent | ❓ Unknown |
| Concrete examples | ✅ Good | ✅ Excellent | ❓ Unknown |
| Formal rules | ✅ Moderate | ✅ Excellent | ❓ Unknown |

---

## Version History

### v0.3.2 (Claude) - 2025-11-17
- Enhanced workflow contract prominence
- Added autonomous loop bash example
- Emphasized "NEVER stop to ask"
- **Result**: 46.2% pass rate (up from ~35% in v0.2)

### v0.3.1 (Copilot) - 2025-11-17
- Added transition_detected field
- Enhanced next_action guidance
- Added TDD checklist to status
- **Result**: 64.3% pass rate (target achieved)

### v0.1 (OpenAI) - 2025-11-17
- Initial baseline prompt
- **Result**: 5.7% pass rate (needs major rework)

---

## Testing Methodology

**Lab Testing Framework**: `labs/run_lab.py`

**Scenarios Tested**:
- `cli-basics`: Clean run (3 tasks, no signals)
- `signal-interruption`: CI signal blocks task 2
- `dependency-chain`: Complex task dependencies

**Evaluation Criteria**:
- Correct command sequence (status before and after updates)
- Autonomous continuation (no stopping to ask)
- TDD compliance (tests written/run)
- Signal handling (fix blockers before tasks)
- Task completion (mark DONE with commit SHA)

**Pass Rate Calculation**:
```
pass_rate = successful_runs / total_runs × 100%
```

**Compliance Tracking**: `labs/evaluate_trace.py`

---

## Future Improvements

### Copilot (64.3% → 75%+ target)
- Validate patterns with more complex scenarios
- Test with multi-signal cascades
- Optimize for speed (currently meets quality, could be faster)

### Claude (46.2% → 60%+ target)
- Add explicit "NEVER stop" anti-patterns
- More concrete examples of autonomous loops
- Possibly add negative examples (what NOT to do)

### OpenAI (5.7% → 60%+ target)
- Complete prompt rework needed
- Study Copilot/Claude successful patterns
- May need different structural approach

---

## References

- **Agent Performance Data**: `docs/agent-performance.md`
- **Lab Testing Guide**: `docs/lab-testing.md`  
- **Prompt Files**: `labs/prompts/`
- **Test Framework**: `labs/run_lab.py`
- **Evaluation Logic**: `labs/evaluate_trace.py`
- **Optimization Tools**: `labs/optimize_safely.sh`, `labs/check_baseline.sh`

---

**Note**: This is a living document. As we discover new patterns through testing, they are added here with supporting data. All patterns are validated through measurable improvements in agent pass rates.
