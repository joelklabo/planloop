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
    print("DSPy Prompt Optimization - Starting Full Run")
    print("=" * 70)
    
    # Configure OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        sys.exit(1)
    
    print("\n✅ Configuring DSPy with OpenAI gpt-4.1...")
    lm = dspy.LM('openai/gpt-4.1', api_key=api_key)
    dspy.configure(lm=lm)
    
    # Load data
    print("\n📊 Loading training data...")
    examples = load_training_data(agent="copilot")
    
    if not examples:
        print("❌ No training data found!")
        sys.exit(1)
    
    print(f"\nLoaded {len(examples)} examples")
    pass_count = sum(1 for ex in examples if ex.score >= 1.0)
    avg_score = sum(ex.score for ex in examples) / len(examples)
    print(f"Baseline: {pass_count}/{len(examples)} passing ({pass_count/len(examples):.1%})")
    print(f"Avg score: {avg_score:.1%}")
    
    # Run optimization
    print("\n" + "=" * 70)
    print("🚀 Starting Optimization (this will take 30-60 minutes)...")
    print("=" * 70)
    print("\nOptimizer: BootstrapFewShot")
    print("Target: Improve Copilot workflow compliance")
    print("Estimated cost: $5-10")
    print("\nProgress will be shown below...\n")
    
    try:
        optimized_agent = optimize_agent_prompt(
            agent="copilot",
            max_bootstrapped_demos=4,
            max_labeled_demos=8,
        )
        
        print("\n" + "=" * 70)
        print("✅ OPTIMIZATION COMPLETE!")
        print("=" * 70)
        print("\nOptimized agent ready for testing")
        print("Next: Extract the optimized prompt and test it!")
        
        # Try to save the optimized program
        output_path = Path("labs/optimized_prompts/copilot_v0.4.0.json")
        output_path.parent.mkdir(exist_ok=True)
        
        # Save the program state
        optimized_agent.save(str(output_path))
        print(f"\n💾 Saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
