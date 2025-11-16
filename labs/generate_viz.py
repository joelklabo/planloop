#!/usr/bin/env python3
"""Generate performance visualization for README."""
from __future__ import annotations

import json
from pathlib import Path


def generate_badge_color(pass_rate: float) -> str:
    """Return badge color based on pass rate."""
    if pass_rate >= 0.8:
        return "brightgreen"
    elif pass_rate >= 0.6:
        return "green"
    elif pass_rate >= 0.4:
        return "yellow"
    elif pass_rate >= 0.2:
        return "orange"
    else:
        return "red"


def generate_performance_doc():
    """Generate agent performance documentation."""
    metrics_file = Path("labs/metrics.json")
    if not metrics_file.exists():
        return "No metrics available yet."
    
    metrics = json.loads(metrics_file.read_text())
    
    total_runs = metrics.get("total_runs", 0)
    latest_run = metrics.get("latest_run", "unknown")
    agents = metrics.get("agents", {})
    agents_by_model = metrics.get("agents_by_model", {})
    
    output = [
        "# 📊 Agent Performance Data\n",
        f"**Total Test Runs:** {total_runs}\n",
        f"\n**Latest Run:** `{latest_run}`\n",
        "\n",
    ]
    
    # Show agent+model badges
    if agents_by_model:
        output.append("## Agent Performance by Model\n\n")
        
        for key in sorted(agents_by_model.keys()):
            stats = agents_by_model[key]
            pass_rate = stats.get("pass_rate", 0.0)
            avg_score = stats.get("avg_score", 0.0)
            color = generate_badge_color(pass_rate)
            
            agent, model = key.split(":", 1)
            label = f"{agent}_{model}".replace("-", "--")
            badge = f"![{key}](https://img.shields.io/badge/{label}-{pass_rate*100:.1f}%25-{color})"
            output.append(f"{badge} **Score:** {avg_score:.1f}/100\n\n")
    
    # Detailed statistics table
    output.append("## Detailed Statistics\n\n")
    output.append("| Agent+Model | Runs | Passes | Fails | Pass Rate | Avg Score | Top Errors |\n")
    output.append("|-------------|------|--------|-------|-----------|-----------|------------|\n")
    
    for key in sorted(agents_by_model.keys()):
        stats = agents_by_model[key]
        runs = stats.get("runs", 0)
        passes = stats.get("passes", 0)
        fails = stats.get("fails", 0)
        pass_rate = stats.get("pass_rate", 0.0)
        avg_score = stats.get("avg_score", 0.0)
        top_errors = stats.get("top_errors", [])
        
        error_str = ", ".join([f"{err} ({count})" for err, count in top_errors[:2]])
        output.append(f"| {key} | {runs} | {passes} | {fails} | {pass_rate*100:.1f}% | {avg_score:.1f} | {error_str} |\n")
    
    output.append("\n## Notes\n\n")
    output.append("- Data collected from automated lab runs testing agent compliance with planloop workflow\n")
    output.append("- **Scores:** 0-100 scale based on workflow compliance (status usage, updates, signal handling)\n")
    output.append("- **Models:** Specific model version used by each agent CLI\n")
    output.append("- **Real agents tested:** Copilot (gpt-5), Claude (sonnet)\n")
    
    return "".join(output)


def main():
    doc = generate_performance_doc()
    
    output_file = Path("docs/agent-performance.md")
    output_file.write_text(doc)
    
    print(f"Generated visualization: {output_file}\n")
    print(doc)


if __name__ == "__main__":
    main()
