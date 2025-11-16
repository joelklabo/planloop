#!/usr/bin/env python3
"""Aggregate lab results into performance metrics."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def analyze_results(results_dir: Path) -> dict[str, Any]:
    """Analyze all lab results and compute aggregate metrics."""
    summaries = []
    
    for result_dir in sorted(results_dir.iterdir()):
        if not result_dir.is_dir():
            continue
        summary_file = result_dir / "summary.json"
        if summary_file.exists():
            try:
                summaries.append(json.load(open(summary_file)))
            except json.JSONDecodeError:
                continue
    
    if not summaries:
        return {"total_runs": 0, "agents": {}}
    
    # Aggregate by agent
    agent_stats = defaultdict(lambda: {"runs": 0, "passes": 0, "fails": 0, "errors": []})
    
    for summary in summaries:
        for agent in summary.get("agents", []):
            name = agent["name"]
            agent_stats[name]["runs"] += 1
            
            compliance = agent.get("compliance", {})
            if compliance.get("pass"):
                agent_stats[name]["passes"] += 1
            else:
                agent_stats[name]["fails"] += 1
                reasons = compliance.get("reasons", ["unknown"])
                for reason in reasons:
                    agent_stats[name]["errors"].append(reason)
    
    # Calculate rates
    for agent, stats in agent_stats.items():
        total = stats["runs"]
        if total > 0:
            stats["pass_rate"] = stats["passes"] / total
            stats["fail_rate"] = stats["fails"] / total
        else:
            stats["pass_rate"] = 0.0
            stats["fail_rate"] = 0.0
        
        # Top errors
        error_counts = defaultdict(int)
        for error in stats["errors"]:
            error_counts[error] += 1
        stats["top_errors"] = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        del stats["errors"]  # Remove raw error list
    
    return {
        "total_runs": len(summaries),
        "latest_run": summaries[-1].get("session", "unknown") if summaries else None,
        "agents": dict(agent_stats),
    }


def main():
    results_dir = Path("labs/results")
    metrics = analyze_results(results_dir)
    
    print(json.dumps(metrics, indent=2))
    
    # Also save to file
    output_file = Path("labs/metrics.json")
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to {output_file}", file=__import__("sys").stderr)


if __name__ == "__main__":
    main()
