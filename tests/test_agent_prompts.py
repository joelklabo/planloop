"""Test agent-specific prompt variations"""
from pathlib import Path


def test_each_agent_has_prompt_file():
    """Each agent should have its own prompt file"""
    agents = ["copilot", "claude", "openai"]

    for agent in agents:
        # Check for versioned prompt files (e.g., copilot-v0.3.1.txt)
        prompt_dir = Path("labs/prompts")
        prompt_files = list(prompt_dir.glob(f"{agent}-v*.txt"))

        assert len(prompt_files) > 0, f"Agent '{agent}' should have at least one versioned prompt file in labs/prompts/"


def test_prompts_are_non_empty():
    """Prompt files should contain actual content"""
    prompt_dir = Path("labs/prompts")

    for prompt_file in prompt_dir.glob("*-v*.txt"):
        content = prompt_file.read_text()
        assert len(content) > 100, f"{prompt_file.name} should have substantial content (>100 chars)"
        assert "planloop" in content.lower(), f"{prompt_file.name} should reference planloop"


def test_agent_scripts_load_from_prompt_files():
    """Agent adapter scripts should load prompts from files, not hardcode them"""
    agents_dir = Path("labs/agents")

    for agent in ["copilot", "claude", "openai"]:
        script_path = agents_dir / f"{agent}_real.sh"
        if not script_path.exists():
            continue

        content = script_path.read_text()

        # Should reference prompts directory or have PLANLOOP_LAB_AGENT_PROMPT override
        assert ("labs/prompts/" in content or "PLANLOOP_LAB_AGENT_PROMPT" in content), \
            f"{script_path.name} should load prompt from file or environment variable"


def test_prompt_versions_documented():
    """Prompt versions should be tracked in baseline.json"""
    import json
    baseline_file = Path("labs/baseline.json")

    with open(baseline_file) as f:
        config = json.load(f)

    for agent in ["copilot", "claude", "openai"]:
        assert agent in config, f"Agent '{agent}' should be in baseline.json"
        assert "version" in config[agent], f"{agent} should have version tracked"
        assert "prompt_file" in config[agent], f"{agent} should have prompt_file tracked"
