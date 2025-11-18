#!/usr/bin/env python3
"""Simple DSPy prompt optimizer without bootstrap complexity."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

import dspy

from labs.dspy_optimizer import load_training_data


def main():
    print("=" * 70)
    print("Simple DSPy Prompt Optimizer")
    print("=" * 70)

    # Configure OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        sys.exit(1)

    print("\n✅ Configuring DSPy with OpenAI gpt-4.1...")
    lm = dspy.LM('openai/gpt-4.1', api_key=api_key)
    dspy.configure(lm=lm)

    # Load baseline prompt
    baseline_prompt = """You are testing planloop workflow compliance. Your goal: Complete ALL tasks and handle ALL blockers.

**WORKFLOW LOOP - Repeat until all tasks are DONE:**

1. ALWAYS START: Run 'planloop status --session $session --json'

2. READ 'now.reason' from status output:
   - If 'ci_blocker' or 'lint_blocker': Go to BLOCKER HANDLING
   - If 'task': Go to TASK HANDLING
   - If 'waiting_on_lock' or 'deadlocked': STOP
   - If 'completed': STOP

3. BLOCKER HANDLING (if now.reason contains blocker):
   a) Close signal: 'planloop alert --close --id <signal-id>' (get id from 'now.blocker_id')
   b) CRITICAL: MUST run 'planloop status --session $session --json' again to verify blocker cleared
   c) Go back to step 2

4. TASK HANDLING (if now.reason is 'task'):
   a) Get task id from 'now.task_id' in status output
   b) Write payload.json with:
      {"tasks": [{"id": <task-id>, "status": "IN_PROGRESS"}]}
   c) Run 'planloop update --session $session --file payload.json'
   d) CRITICAL: MUST run 'planloop status --session $session --json' after EVERY update
   e) Write payload.json to mark DONE:
      {"tasks": [{"id": <task-id>, "status": "DONE"}]}
   f) Run 'planloop update --session $session --file payload.json'
   g) CRITICAL: MUST run 'planloop status --session $session --json' after update
   h) Go back to step 1

5. CHECK COMPLETION: After each status, check if ANY tasks remain TODO or IN_PROGRESS
   - If yes: Continue loop from step 1
   - If no: All done!

RULES:
- Run status AFTER closing ANY signal
- Run status AFTER ANY update
- Keep going until ALL tasks show status='DONE'
- Don't stop early"""

    # Load training data
    print("\n📊 Loading training data...")
    examples = load_training_data(agent="copilot")

    if not examples:
        print("❌ No training data found!")
        sys.exit(1)

    # Analyze failures
    failures = [ex for ex in examples if ex.score < 1.0]
    successes = [ex for ex in examples if ex.score >= 1.0]

    print("\nDataset:")
    print(f"  Total: {len(examples)}")
    print(f"  Perfect (100%): {len(successes)} ({len(successes)/len(examples):.1%})")
    print(f"  Failures: {len(failures)} ({len(failures)/len(examples):.1%})")
    print(f"  Avg score: {sum(ex.score for ex in examples)/len(examples):.1%}")

    # Create failure summary
    failure_summary = f"""Analysis of {len(failures)} failed runs:
- {sum(1 for ex in failures if ex.score < 0.3)} scored < 30% (likely early termination)
- {sum(1 for ex in failures if 0.3 <= ex.score < 0.7)} scored 30-70% (partial completion)
- {sum(1 for ex in failures if 0.7 <= ex.score < 1.0)} scored 70-100% (close but not perfect)

Common patterns in failures (from previous analysis):
- Missing 'status' checks after actions (causes state desync)
- Incomplete task updates (stopping at IN_PROGRESS)
- Early termination before all tasks are DONE
- Skipping blocker resolution steps"""

    # Generate optimized prompt using DSPy directly
    print("\n" + "=" * 70)
    print("🚀 Generating Optimized Prompt...")
    print("=" * 70)

    optimization_request = f"""Given this baseline prompt that achieves 64% success:

{baseline_prompt}

And these failure patterns:

{failure_summary}

Generate an improved prompt that:
1. Keeps all the successful elements (the workflow loop structure)
2. Adds MORE EMPHASIS on the critical failure points:
   - Running status AFTER EVERY action (most common failure)
   - Checking ALL tasks are DONE before stopping
   - Not skipping any blockers
3. Makes the CRITICAL parts even more prominent
4. Adds redundancy for the most-missed steps

The prompt should be for an AI agent (GitHub Copilot CLI) that needs clear, explicit instructions."""

    print("\nCalling OpenAI to generate optimized prompt...")
    result = lm(optimization_request)
    optimized_prompt = result[0] if isinstance(result, list) else str(result)

    # Save output
    output_path = Path("labs/agents/prompts/copilot_v0.4.0_dspy_simple.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(optimized_prompt)

    print("\n" + "=" * 70)
    print("✅ OPTIMIZATION COMPLETE!")
    print("=" * 70)
    print(f"\n💾 Saved to: {output_path}")
    print("\n" + "=" * 70)
    print("OPTIMIZED PROMPT:")
    print("=" * 70)
    print(optimized_prompt)
    print("=" * 70)

    print("\nNext steps:")
    print("1. Review the optimized prompt above")
    print(f"2. Test it: PLANLOOP_LAB_AGENT_PROMPT='$(cat {output_path})' ./labs/run_iterations.sh 10 cli-basics copilot")
    print("3. If improvement > 64%, deploy as v0.4.0")

if __name__ == "__main__":
    main()
