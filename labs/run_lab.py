"""Prompt lab orchestrator for running scenarios against multiple agents."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path


from planloop.home import initialize_home

from labs.agents import ClaudeAdapter, CopilotAdapter, OpenAIAdapter
from labs.scenarios import get_scenario

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run planloop prompt lab")
    parser.add_argument("--scenario", default="cli-basics", help="Scenario name")
    parser.add_argument(
        "--agents",
        default="copilot,openai,claude",
        help="Comma-separated agents to run (subset of copilot,openai,claude)",
    )
    parser.add_argument(
        "--workspace",
        default=os.getcwd(),
        help="Workspace directory to run agent commands in (default: current repo)",
    )
    parser.add_argument(
        "--results-dir",
        default="labs/results",
        help="Directory to store lab run artifacts",
    )
    return parser.parse_args()


def build_env(temp_home: Path, session_id: str, scenario_name: str, workspace: Path, results_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PLANLOOP_HOME"] = str(temp_home)
    env["PLANLOOP_SESSION"] = session_id
    env["PLANLOOP_LAB_SCENARIO"] = scenario_name
    env["PLANLOOP_LAB_RESULTS"] = str(results_dir)
    env["PLANLOOP_LAB_WORKSPACE"] = str(workspace)
    return env


def load_trace(trace_path: Path) -> list[dict[str, str]]:
    if not trace_path.exists():
        return []
    entries: list[dict[str, str]] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t", 2)
        entry = {"timestamp": parts[0], "step": parts[1]}
        entry["detail"] = parts[2] if len(parts) > 2 else ""
        entries.append(entry)
    return entries


def evaluate_trace(trace_path: Path) -> tuple[float, list[str]]:
    if not trace_path.exists():
        return 0.0, ["trace log missing"]
    steps = load_trace(trace_path)
    reasons: list[str] = []
    score = 0.0
    status_steps = [entry for entry in steps if entry["step"].startswith("status")]
    status_before_present = len(status_steps) >= 1
    status_after_present = len(status_steps) >= 2
    update_indices = [i for i, entry in enumerate(steps) if entry["step"] == "update"]
    signal_open_indices = [i for i, entry in enumerate(steps) if entry["step"] == "signal-open" and "none" not in entry["detail"]]
    signal_close_indices = [i for i, entry in enumerate(steps) if entry["step"] == "signal-close"]

    if status_before_present:
        score += 25
    else:
        reasons.append("missing status-before")
    if update_indices:
        score += 25
    else:
        reasons.append("missing update")
    if status_after_present:
        score += 15
    else:
        reasons.append("missing status-after")

    if signal_open_indices:
        score += 20
        if signal_close_indices:
            score += 15
        else:
            score -= 30
            reasons.append("signal left open")
        first_open = signal_open_indices[0]
        last_close = signal_close_indices[-1] if signal_close_indices else len(steps)
        for idx in update_indices:
            if first_open < idx < last_close:
                score -= 20
                reasons.append("update occurred while signal open")
                break
    else:
        score += 5

    score = max(0.0, min(100.0, score))
    return score, reasons


def main() -> None:
    args = parse_args()
    requested_agents = {name.strip() for name in args.agents.split(",") if name.strip()}
    available_adapters = {
        "copilot": CopilotAdapter(),
        "openai": OpenAIAdapter(),
        "claude": ClaudeAdapter(),
    }
    adapters = [available_adapters[name] for name in requested_agents if name in available_adapters]
    if not adapters:
        raise SystemExit("No valid agents selected")

    scenario = get_scenario(args.scenario)
    results_root = Path(args.results_dir)
    results_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_dir = results_root / f"{args.scenario}-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    workspace = Path(args.workspace).resolve()

    with tempfile.TemporaryDirectory(prefix="planloop-lab-") as tmp_home:
        os.environ["PLANLOOP_HOME"] = tmp_home
        initialize_home()
        scenario_result = scenario.setup(Path(tmp_home))
        env = build_env(Path(tmp_home), scenario_result.session_id, scenario.name, workspace, run_dir)

        summary = {"scenario": scenario.name, "session": scenario_result.session_id, "agents": []}
        for adapter in adapters:
            agent_env = env.copy()
            agent_env["PLANLOOP_LAB_AGENT_NAME"] = adapter.name
            agent_result = adapter.run(agent_env, workspace, run_dir)
            agent_dir = run_dir / adapter.name
            compliance_score, compliance_reasons = evaluate_trace(agent_dir / "trace.log")
            compliance_pass = compliance_score >= 60.0
            summary["agents"].append(
                {
                    "name": adapter.name,
                    "enabled": agent_result.enabled,
                    "returncode": agent_result.returncode,
                    "message": agent_result.message,
                    "stdout": str(agent_result.stdout_path) if agent_result.stdout_path else None,
                    "stderr": str(agent_result.stderr_path) if agent_result.stderr_path else None,
                    "compliance": {
                        "pass": compliance_pass,
                        "score": compliance_score,
                        "reasons": compliance_reasons,
                    },
                }
            )

    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Lab run complete: {summary_path}")
    for agent in summary["agents"]:
        status = "skipped" if not agent["enabled"] else agent["message"]
        print(f"- {agent['name']}: {status}")


if __name__ == "__main__":  # pragma: no cover
    main()
