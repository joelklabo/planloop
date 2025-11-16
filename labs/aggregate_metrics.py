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
        return {"total_runs": 0, "agents": {}, "agents_by_model": {}}
    
    # Aggregate by agent only (legacy)
    agent_stats = defaultdict(lambda: {"runs": 0, "passes": 0, "fails": 0, "errors": []})
    
    # Aggregate by agent+model
    agent_model_stats = defaultdict(lambda: {"runs": 0, "passes": 0, "fails": 0, "scores": [], "errors": []})
    
    for summary in summaries:
        for agent in summary.get("agents", []):
            name = agent["name"]
            agent_stats[name]["runs"] += 1
            
            compliance = agent.get("compliance", {})
            score = compliance.get("score", 0.0)
            passed = compliance.get("pass", False)
            
            # Extract model from trace if available
            model = "unknown"
            run_dir_name = result_dir.name
            trace_path = result_dir / name / "trace.log"
            if trace_path.exists():
                try:
                    for line in trace_path.read_text().splitlines():
                        if "agent-config" in line and "model=" in line:
                            model = line.split("model=")[1].strip()
                            break
                except Exception:
                    pass
            
            # Track by agent+model
            model_key = f"{name}:{model}"
            agent_model_stats[model_key]["runs"] += 1
            agent_model_stats[model_key]["scores"].append(score)
            
            if passed:
                agent_stats[name]["passes"] += 1
                agent_model_stats[model_key]["passes"] += 1
            else:
                agent_stats[name]["fails"] += 1
                agent_model_stats[model_key]["fails"] += 1
                reasons = compliance.get("reasons", ["unknown"])
                for reason in reasons:
                    agent_stats[name]["errors"].append(reason)
                    agent_model_stats[model_key]["errors"].append(reason)
    
    # Calculate rates for agent-only stats
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
        del stats["errors"]
    
    # Calculate rates for agent+model stats
    for key, stats in agent_model_stats.items():
        total = stats["runs"]
        if total > 0:
            stats["pass_rate"] = stats["passes"] / total
            stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"])
        else:
            stats["pass_rate"] = 0.0
            stats["avg_score"] = 0.0
        
        # Top errors
        error_counts = defaultdict(int)
        for error in stats["errors"]:
            error_counts[error] += 1
        stats["top_errors"] = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        del stats["errors"]
        del stats["scores"]
    
    return {
        "total_runs": len(summaries),
        "latest_run": summaries[-1].get("session", "unknown") if summaries else None,
        "agents": dict(agent_stats),
        "agents_by_model": dict(agent_model_stats),
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
