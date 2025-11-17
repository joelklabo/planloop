# Agent Prompting Best Practices

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
- 64.3% pass rate ✅ WORKING WELL
- Avg score: 51.5/100

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
**v0.3.1 - STABLE - DO NOT MODIFY**
- Pass rate: 64.3%
- Numbered lists + CRITICAL markers = working perfectly
- **Any changes risk regression**

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

## Maintenance

**When to Update**:
- After discovering new techniques
- When performance plateaus
- After agent model updates
- When research reveals new patterns

**Version History**:
- v1.0 (2025-11-17): Initial guide based on 218 test runs + research
