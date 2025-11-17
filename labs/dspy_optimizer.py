"""DSPy-based prompt optimization for planloop agents.

This module wraps our existing test infrastructure with DSPy to automatically
optimize agent prompts based on workflow compliance metrics.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import dspy


class WorkflowComplianceSignature(dspy.Signature):
    """Complete all planloop workflow tasks with proper status tracking."""
    
    session_id = dspy.InputField(desc="Session ID for the workflow")
    scenario_name = dspy.InputField(desc="Scenario to execute")
    agent_instructions = dspy.OutputField(desc="Instructions for the agent to follow")


class WorkflowAgent(dspy.Module):
    """Agent that completes workflow tasks."""
    
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(WorkflowComplianceSignature)
    
    def forward(self, session_id: str, scenario_name: str):
        """Generate instructions for workflow completion."""
        result = self.generate(session_id=session_id, scenario_name=scenario_name)
        return result.agent_instructions


def workflow_compliance_metric(example: dspy.Example, prediction: Any, trace=None) -> float:
    """
    Metric function that evaluates workflow compliance.
    
    Args:
        example: DSPy example containing session_id and scenario_name
        prediction: Generated instructions from the agent
        trace: Optional trace from DSPy
    
    Returns:
        Float score 0.0-1.0 representing compliance (0-100 score / 100)
    """
    # For now, we'll run the actual agent with the predicted instructions
    # In production, this would execute the full test harness
    
    # TODO: Implement actual test execution
    # For now, return a placeholder based on historical data
    # This would be replaced with actual run_lab.py execution
    
    # Placeholder: analyze the prediction quality
    score = 0.0
    
    # Check if instructions mention key requirements
    if "status" in prediction.lower():
        score += 0.3
    if "update" in prediction.lower():
        score += 0.2
    if "blocker" in prediction.lower() or "signal" in prediction.lower():
        score += 0.2
    if "done" in prediction.lower():
        score += 0.15
    if "loop" in prediction.lower() or "repeat" in prediction.lower():
        score += 0.15
    
    return score


def load_training_data(results_dir: str = "labs/results", agent: str = "copilot") -> list[dspy.Example]:
    """
    Load historical test results as DSPy training examples.
    
    Args:
        results_dir: Directory containing test results
        agent: Agent name to load data for
    
    Returns:
        List of DSPy examples
    """
    examples = []
    results_path = Path(results_dir)
    
    # Find all result directories
    for result_dir in results_path.glob("cli-basics-*/"):
        summary_file = result_dir / "summary.json"
        if not summary_file.exists():
            continue
        
        try:
            with open(summary_file) as f:
                summary = json.load(f)
            
            # Check if this run has our target agent
            if agent not in summary.get("results", {}):
                continue
            
            agent_result = summary["results"][agent]
            if not agent_result:
                continue
            
            # Get the evaluation score
            evaluation = agent_result.get("evaluation", {})
            score = evaluation.get("score", 0)
            
            # Create example
            example = dspy.Example(
                session_id=summary.get("session_id", ""),
                scenario_name="cli-basics",
                score=score / 100.0,  # Normalize to 0-1
            ).with_inputs("session_id", "scenario_name")
            
            examples.append(example)
            
        except (json.JSONDecodeError, KeyError) as e:
            continue
    
    print(f"Loaded {len(examples)} training examples for {agent}")
    return examples


def optimize_agent_prompt(
    agent: str = "copilot",
    max_bootstrapped_demos: int = 4,
    max_labeled_demos: int = 8,
    num_trials: int = 50
) -> dspy.Module:
    """
    Optimize agent prompt using DSPy.
    
    Args:
        agent: Agent name to optimize for
        max_bootstrapped_demos: Max examples to bootstrap
        max_labeled_demos: Max labeled examples to use
        num_trials: Number of optimization trials
    
    Returns:
        Optimized DSPy module
    """
    # Load training data
    trainset = load_training_data(agent=agent)
    
    if len(trainset) < 10:
        raise ValueError(f"Need at least 10 examples, got {len(trainset)}")
    
    # Split into train/dev
    split_point = int(len(trainset) * 0.8)
    train_examples = trainset[:split_point]
    dev_examples = trainset[split_point:]
    
    print(f"Training on {len(train_examples)} examples")
    print(f"Validating on {len(dev_examples)} examples")
    
    # Initialize the agent
    agent_module = WorkflowAgent()
    
    # Configure optimizer
    # Using BootstrapFewShot as a starting point (simpler than MIPROv2)
    optimizer = dspy.BootstrapFewShot(
        metric=workflow_compliance_metric,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=max_labeled_demos,
    )
    
    # Compile/optimize
    print("Running optimization...")
    optimized_agent = optimizer.compile(
        agent_module,
        trainset=train_examples,
    )
    
    # Evaluate on dev set
    print("\nEvaluating on dev set...")
    scores = []
    for example in dev_examples[:5]:  # Test on first 5
        pred = optimized_agent(
            session_id=example.session_id,
            scenario_name=example.scenario_name
        )
        score = workflow_compliance_metric(example, pred)
        scores.append(score)
        print(f"  Example: {score:.2f}")
    
    avg_score = sum(scores) / len(scores) if scores else 0
    print(f"\nAverage dev score: {avg_score:.2%}")
    
    return optimized_agent


if __name__ == "__main__":
    # Configure DSPy to use a local LM or API
    # For now, we'll use a placeholder
    # In production, this would connect to actual LLM
    
    print("DSPy Prompt Optimizer for Planloop")
    print("=" * 60)
    
    # TODO: Configure LM
    # lm = dspy.OpenAI(model="gpt-4")
    # dspy.settings.configure(lm=lm)
    
    print("\nStep 1: Loading training data...")
    examples = load_training_data(agent="copilot")
    
    print(f"\nStep 2: Analyzing {len(examples)} historical runs...")
    pass_count = sum(1 for ex in examples if ex.score >= 1.0)
    avg_score = sum(ex.score for ex in examples) / len(examples) if examples else 0
    print(f"  Pass rate: {pass_count}/{len(examples)} ({pass_count/len(examples):.1%})")
    print(f"  Avg score: {avg_score:.1%}")
    
    # TODO: Run optimization when LM is configured
    # print("\nStep 3: Running optimization...")
    # optimized = optimize_agent_prompt(agent="copilot")
    
    print("\n✅ Setup complete! Next: Configure LM and run optimization")
