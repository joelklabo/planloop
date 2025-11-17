#!/usr/bin/env python3
"""Run DSPy optimization for a specific agent."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from labs.dspy_optimizer import optimize_agent_prompt, load_training_data
import os
from dotenv import load_dotenv
load_dotenv()

import dspy

def main():
    print("=" * 70)
    print("DSPy Prompt Optimization - v2 (Fixed Signature)")
    print("=" * 70)
    
    # Configure OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        sys.exit(1)
    
    print("\n✅ Configuring DSPy with OpenAI gpt-4.1...")
    lm = dspy.LM('openai/gpt-4.1', api_key=api_key)
    dspy.configure(lm=lm)
    
    # Load baseline prompt from copilot_real.sh
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
    
    # Load data
    print("\n📊 Loading training data...")
    examples = load_training_data(agent="copilot")
    
    if not examples:
        print("❌ No training data found!")
        sys.exit(1)
    
    print(f"\nLoaded {len(examples)} examples")
    pass_count = sum(1 for ex in examples if ex.score >= 1.0)
    avg_score = sum(ex.score for ex in examples) / len(examples)
    print(f"Baseline: {pass_count}/{len(examples)} perfect ({pass_count/len(examples):.1%})")
    print(f"Avg score: {avg_score:.1%}")
    
    # Run optimization
    print("\n" + "=" * 70)
    print("🚀 Starting Optimization v2 (with proper context)...")
    print("=" * 70)
    print("\nOptimizer: BootstrapFewShot")
    print("Input: v0.3.1 prompt (64% success)")
    print("Goal: Generate v0.4.0 that addresses failure patterns")
    print("Estimated cost: $3-5")
    print("\nProgress will be shown below...\n")
    
    try:
        optimized_agent, best_prompt = optimize_agent_prompt(
            agent="copilot",
            baseline_prompt=baseline_prompt,
            max_bootstrapped_demos=4,
            max_labeled_demos=8,
        )
        
        print("\n" + "=" * 70)
        print("✅ OPTIMIZATION COMPLETE!")
        print("=" * 70)
        print("\nGenerated optimized prompt")
        
        # Save the optimized prompt
        output_path = Path("labs/agents/prompts/copilot_v0.4.0_dspy.txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(best_prompt)
        
        print(f"\n💾 Saved optimized prompt to: {output_path}")
        print("\n" + "=" * 70)
        print("OPTIMIZED PROMPT:")
        print("=" * 70)
        print(best_prompt)
        print("=" * 70)
        
        # Save the DSPy module state
        module_path = Path("labs/optimized_prompts/copilot_v0.4.0_module.json")
        module_path.parent.mkdir(exist_ok=True)
        optimized_agent.save(str(module_path))
        print(f"\n💾 Saved DSPy module to: {module_path}")
        
        print("\nNext steps:")
        print("1. Review the optimized prompt above")
        print("2. Test it with: PLANLOOP_LAB_AGENT_PROMPT='$(cat labs/agents/prompts/copilot_v0.4.0_dspy.txt)' ./labs/run_iterations.sh 10 cli-basics copilot")
        print("3. If better than 64%, deploy as v0.4.0")
        
    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
