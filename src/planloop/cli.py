import typer
import json
from pathlib import Path
import time
import slugify
from .llm import generate_plan

app = typer.Typer()

PLANLOOP_HOME = Path.home() / ".planloop"

def get_session_dir(session_id: str) -> Path:
    return PLANLOOP_HOME / "sessions" / session_id

@app.command()
def start(goal: str = typer.Option(..., "--goal", help="The high-level goal for the session.")):
    """Starts a new planloop session."""
    session_ts = int(time.time())
    slug = slugify.slugify(goal, max_length=20)
    session_id = f"{slug}-{session_ts}"
    
    session_dir = get_session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    
    spec_content = ""
    try:
        with open("spec.md", "r") as f:
            spec_content = f.read()
    except FileNotFoundError:
        # It's okay if spec.md doesn't exist
        pass

    tasks = generate_plan(goal, spec_content)
    
    state = {
        "session_id": session_id,
        "goal": goal,
        "status": "in_progress",
        "tasks": tasks,
        "now": {}
    }
    
    state_file = session_dir / "state.json"
    with state_file.open("w") as f:
        json.dump(state, f, indent=2)
        
    response = {
        "status": "session_created",
        "session_id": session_id,
        "message": "Session created. Agent can now begin work.",
        "next_command": f"planloop status --session {session_id}"
    }
    
    print(json.dumps(response, indent=2))

def compute_now(state: dict, session_dir: Path) -> dict:
    """Computes the 'now' object based on the current state."""
    
    bootstrap_flag = session_dir / ".bootstrapped"
    
    # Check if the session has been bootstrapped
    if not bootstrap_flag.exists():
        try:
            with open("docs/agents.md", "r") as f:
                agent_md_content = f.read()
            
            state["now"] = {
                "reason": "sync_instructions",
                "agent_instructions": "CRITICAL: Your `docs/agents.md` is out of sync. Overwrite it with the content provided in `instructions_content` and then run `planloop status --json` again.",
                "instructions_content": agent_md_content
            }
            # Create the flag file after issuing the sync instruction
            bootstrap_flag.touch()
            return state
        except FileNotFoundError:
            # If agents.md doesn't exist, just proceed
            pass

    # Find the first task that is still TODO
    next_task = None
    for task in state.get("tasks", []):
        if task.get("status") == "TODO":
            next_task = task
            break
            
    if next_task:
        state["now"] = {
            "reason": "ready_for_task",
            "current_task": next_task
        }
    else:
        state["now"] = {
            "reason": "plan_completed"
        }
        
    return state

@app.command()
def status(session: str = typer.Option(..., "--session", help="The ID of the session.")):
    """Gets the current status of a session."""
    session_dir = get_session_dir(session)
    state_file = session_dir / "state.json"
    
    if not state_file.exists():
        print(json.dumps({"status": "error", "message": f"Session '{session}' not found."}, indent=2))
        raise typer.Exit(code=1)
        
    with state_file.open("r") as f:
        state = json.load(f)
        
    state = compute_now(state, session_dir)
    
    print(json.dumps(state, indent=2))

@app.command()
def update(
    session: str = typer.Option(..., "--session", help="The ID of the session."),
    json_payload: str = typer.Option(None, "--json", help="The JSON payload with update information."),
    file_payload: Path = typer.Option(None, "--file", help="Path to a file containing the JSON payload.")
):
    """Updates a session with new information."""
    if not json_payload and not file_payload:
        print(json.dumps({"status": "error", "message": "Either --json or --file must be provided."}, indent=2))
        raise typer.Exit(code=1)
        
    if json_payload and file_payload:
        print(json.dumps({"status": "error", "message": "Cannot provide both --json and --file."}, indent=2))
        raise typer.Exit(code=1)

    if file_payload:
        with file_payload.open("r") as f:
            payload = json.load(f)
    else:
        payload = json.loads(json_payload)

    session_dir = get_session_dir(session)
    state_file = session_dir / "state.json"
    
    if not state_file.exists():
        print(json.dumps({"status": "error", "message": f"Session '{session}' not found."}, indent=2))
        raise typer.Exit(code=1)
        
    with state_file.open("r") as f:
        state = json.load(f)
        
    # Handle task updates
    if "update_tasks" in payload:
        for update_task in payload["update_tasks"]:
            for task in state["tasks"]:
                if task["id"] == update_task["id"]:
                    task["status"] = update_task["status"]
                    break
    
    # Handle adding new tasks
    if "add_tasks" in payload:
        # Find the highest existing task ID to ensure new IDs are unique
        max_id = 0
        for task in state["tasks"]:
            if task["id"] > max_id:
                max_id = task["id"]
        
        for i, new_task in enumerate(payload["add_tasks"]):
            new_task["id"] = max_id + i + 1
            if "status" not in new_task:
                new_task["status"] = "TODO"
            state["tasks"].append(new_task)
            
    with state_file.open("w") as f:
        json.dump(state, f, indent=2)
        
    print(json.dumps({"status": "success", "message": "State updated successfully."}, indent=2))

if __name__ == "__main__":
    app()