#!/usr/bin/env python3
"""Update README.md with latest metrics."""
from __future__ import annotations

import json
import re
from pathlib import Path


def update_readme(metrics: dict) -> bool:
    """Update README with latest metrics. Returns True if changed."""
    readme_path = Path("README.md")
    content = readme_path.read_text()
    
    # Generate new metrics section
    total_runs = metrics["total_runs"]
    latest_run = metrics["latest_run"]
    
    badges = []
    table_rows = []
    
    for agent_name, stats in sorted(metrics["agents"].items()):
        pass_rate = stats["pass_rate"] * 100
        color = "green" if pass_rate >= 70 else "yellow" if pass_rate >= 40 else "red"
        badge = f"![{agent_name}](https://img.shields.io/badge/{agent_name}-{pass_rate:.1f}%25-{color})"
        badges.append(badge)
        
        top_errors = ", ".join([f"{err} ({count})" for err, count in stats["top_errors"][:2]])
        table_rows.append(
            f"| {agent_name} | {stats['runs']} | {stats['passes']} | "
            f"{stats['fails']} | {pass_rate:.1f}% | {top_errors} |"
        )
    
    new_section = f"""## 📊 Agent Performance Data

**Total Test Runs:** {total_runs} | **Latest:** `{latest_run}`

### Compliance Rates
{' '.join(badges)}

| Agent | Runs | Passes | Fails | Pass Rate | Top Errors |
|-------|------|--------|-------|-----------|------------|
{chr(10).join(table_rows)}

*Data from automated lab runs testing workflow compliance. See [docs/agent-performance.md](docs/agent-performance.md) for details. Stats auto-update via GitHub Actions.*
"""
    
    # Replace the section between "## 📊 Agent Performance Data" and the next "##"
    pattern = r'## 📊 Agent Performance Data.*?(?=\n## )'
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, new_section.rstrip() + '\n\n', content, flags=re.DOTALL)
        
        if new_content != content:
            readme_path.write_text(new_content)
            print("README.md updated with latest metrics")
            return True
        else:
            print("No changes needed")
            return False
    else:
        print("Warning: Could not find metrics section in README")
        return False


def main():
    metrics_file = Path("labs/metrics.json")
    if not metrics_file.exists():
        print("Error: metrics.json not found")
        return 1
    
    metrics = json.load(open(metrics_file))
    update_readme(metrics)
    return 0


if __name__ == "__main__":
    exit(main())
