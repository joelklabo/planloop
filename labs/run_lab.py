"""Prompt lab orchestrator for running scenarios against multiple agents."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from planloop.home import initialize_home

from .agents import ClaudeAdapter, CopilotAdapter, OpenAIAdapter
from .scenarios import get_scenario


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
            agent_result = adapter.run(env, workspace, run_dir)
            summary["agents"].append(
                {
                    "name": adapter.name,
                    "enabled": agent_result.enabled,
                    "returncode": agent_result.returncode,
                    "message": agent_result.message,
                    "stdout": str(agent_result.stdout_path) if agent_result.stdout_path else None,
                    "stderr": str(agent_result.stderr_path) if agent_result.stderr_path else None,
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
