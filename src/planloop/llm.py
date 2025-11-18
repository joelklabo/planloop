import os
import json
from openai import OpenAI

# Ensure the API key is set, otherwise raise an error
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = OpenAI(api_key=api_key)

def generate_plan(goal: str, spec_content: str) -> list:
    """
    Calls the LLM to decompose the goal and spec into a task list.
    """
    
    print("Decomposing goal with OpenAI... (this may take a moment)")

    # This is the "P-1: Plan Decomposition Prompt"
    prompt = f"""
    You are an expert software engineering project manager specializing in CLI tools.
    Your job is to take a high-level goal and a specification document and break it down
    into a detailed, actionable task list in JSON format.

    The tool you are planning for is a command-line interface (CLI) tool that operates on the local filesystem.
    It does NOT have a database, a web server, or a frontend UI unless the goal explicitly asks for one.
    Your plan should focus on implementing CLI commands, file-based session management, and local file operations.

    Follow all principles from the `planning-guide.md`. Specifically:
    - Tasks must be small and have a single responsibility.
    - Each task must have a `title`, `type`, `dependencies`, `context_hints`, and `relevant_file_paths`.
    - `type` must be one of: 'feature', 'bugfix', 'chore', 'test'.
    - `dependencies` must be a list of task IDs.
    - `context_hints` must be a list of strings.
    - `relevant_file_paths` must be a list of strings that exist in the project.
    - The plan must not have circular dependencies.

    THE GOAL: "{goal}"

    THE SPECIFICATION DOCUMENT (`spec.md`):
    ---
    {spec_content}
    ---

    Respond ONLY with a valid JSON object containing a single key "tasks", which is a list of task objects.
    Do not include any other text, explanation, or markdown formatting.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a project planning assistant that only outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            return []
            
        plan_data = json.loads(content)
        tasks = plan_data.get("tasks", [])
        
        # Simple validation and ID assignment
        for i, task in enumerate(tasks):
            task["id"] = i + 1
            if "status" not in task:
                task["status"] = "TODO"

        # Here we would run the P-2 "LLM-as-a-Judge" and other quality gates.
        # For now, we will just return the generated tasks.
        
        return tasks

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return []

