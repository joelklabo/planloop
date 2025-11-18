import json
from src.planloop.llm import generate_plan

spec_content = ""
with open("spec.md", "r") as f:
    spec_content = f.read()

new_tasks = generate_plan(
    "Implement the features for the planloop CLI tool itself, as described in the attached spec.md file. Focus on the CLI commands and file-based session management. Do not generate tasks for databases, APIs, or frontends.",
    spec_content
)

with open("new_plan.json", "w") as f:
    json.dump({"tasks": new_tasks}, f, indent=2)
