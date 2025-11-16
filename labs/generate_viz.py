#!/usr/bin/env python3
"""Generate markdown visualization from metrics."""
from __future__ import annotations

import json
from pathlib import Path


def generate_badge_url(label: str, message: str, color: str) -> str:
    """Generate shields.io badge URL."""
    return f"https://img.shields.io/badge/{label}-{message}-{color}"


def generate_markdown(metrics: dict) -> str:
    """Generate markdown visualization."""
    md = []
    
    md.append("# 📊 Agent Performance Data\n")
    md.append(f"**Total Test Runs:** {metrics['total_runs']}\n")
    md.append(f"**Latest Run:** `{metrics['latest_run']}`\n")
    md.append("")
    
    # Agent badges
    md.append("## Agent Compliance Rates\n")
    for agent_name, stats in sorted(metrics["agents"].items()):
        pass_rate = stats["pass_rate"] * 100
        color = "green" if pass_rate >= 70 else "yellow" if pass_rate >= 40 else "red"
        badge = generate_badge_url(agent_name, f"{pass_rate:.1f}%25", color)
        md.append(f"![{agent_name}]({badge})")
    md.append("")
    
    # Detailed table
    md.append("## Detailed Statistics\n")
    md.append("| Agent | Runs | Passes | Fails | Pass Rate | Top Errors |")
    md.append("|-------|------|--------|-------|-----------|------------|")
    
    for agent_name, stats in sorted(metrics["agents"].items()):
        pass_rate = f"{stats['pass_rate']*100:.1f}%"
        top_errors = ", ".join([f"{err} ({count})" for err, count in stats["top_errors"][:2]])
        md.append(
            f"| {agent_name} | {stats['runs']} | {stats['passes']} | "
            f"{stats['fails']} | {pass_rate} | {top_errors} |"
        )
    md.append("")
    
    # Performance trend note
    md.append("## Notes\n")
    md.append("- Data collected from automated lab runs testing agent compliance with planloop workflow")
    md.append("- Metrics track: status command usage, update command usage, proper workflow sequence")
    md.append("- Updated automatically via GitHub Actions (see `.github/workflows/update-metrics.yml`)")
    md.append("")
    
    return "\n".join(md)


def main():
    metrics_file = Path("labs/metrics.json")
    if not metrics_file.exists():
        print("Error: metrics.json not found. Run aggregate_metrics.py first.")
        return 1
    
    metrics = json.load(open(metrics_file))
    markdown = generate_markdown(metrics)
    
    # Save to file
    output_file = Path("docs/agent-performance.md")
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(markdown)
    
    print(f"Generated visualization: {output_file}")
    print("\n" + markdown)
    
    return 0


if __name__ == "__main__":
    exit(main())
