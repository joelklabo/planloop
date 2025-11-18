# planloop Specification

This document contains the complete specification for the `planloop` system, combining the workflow, API contract, planning guide, and prompt catalog.

---
# Part 1: Agent Onboarding & Workflow

This document describes the concrete, end-to-end workflow for a new `planloop` session. It is broken into a one-time **Onboarding Phase** and the repeating **Execution Loop**.

The key principle is that an agent's work is more reliable when it first builds a high-quality plan with **context hints**, and then executes that plan step-by-step.

---

### Onboarding Phase: From Goal to Plan

This phase gets the agent and the plan set up correctly.

#### **Step 1: User Kick-off**

The user initializes a session with a high-level goal.

```bash
$ planloop start --goal "Implement the features described in spec.md"
```

---

#### **Step 2: Agent's First Contact & Instruction Sync (Self-Bootstrapping)**

The agent makes its first call to `status` and is directed to sync its own instructions (`docs/agents.md`) to ensure it has the latest rules.

1.  **Agent runs `status`:**
    ```bash
    $ planloop status --json
    ```

2.  **`planloop` commands an instruction sync:**
    ```json
    {
      "now": {
        "reason": "sync_instructions",
        "instructions_content": "[The full, correct content of the canonical agents.md]"
      }
    }
    ```

3.  **Agent updates its own rules** by overwriting `docs/agents.md`.

---

#### **Step 3: The Plan Decomposition Task (The "Thinking" Phase)**

With the correct rules, the agent now creates a detailed, context-rich plan. This is a slow and deliberate phase.

1.  **Agent runs `status` again:**
    ```bash
    $ planloop status --json
    ```

2.  **`planloop` provides the "meta-task" to create the plan:**
    ```json
    {
      "now": {
        "reason": "ready_for_task",
        "current_task": {
          "id": 1,
          "title": "Decompose the goal 'Implement the features described in spec.md' into a detailed task list for planloop.",
          "status": "TODO"
        }
      }
    }
    ```

3.  **Agent generates the plan with Context Hints:**
    The agent reads `spec.md` and creates a list of tasks. Crucially, for each task, it includes an array of `context_hints` that will guide its future self.

4.  **Agent submits the new plan:**
    It uses `update` to add the new tasks (with hints) and mark the decomposition task as `DONE`.
    ```bash
    $ planloop update --json '{
        "add_tasks": [
          {
            "title": "Set up database schema",
            "context_hints": [
              "Read the 'Database Schema' section in `spec.md`.",
              "Review existing models in `src/models/` for conventions."
            ]
          },
          {
            "title": "Create API endpoints for users",
            "context_hints": [
              "Endpoints should follow the pattern in `src/api/existing_routes.py`.",
              "Refer to the 'User API' section of `spec.md` for required fields."
            ]
          }
        ],
        "update_tasks": [
          {"id": 1, "status": "DONE"}
        ]
      }'
    ```

---

### Execution Loop Phase (The "Doing" Phase)

The agent now efficiently cycles through the well-defined plan.

#### **Step 4: Normal Task Loop Begins**

1.  **Agent runs `status` to get its first real task:**
    ```bash
    $ planloop status --json
    ```

2.  **`planloop` returns the next task, complete with hints:**
    ```json
    {
      "now": {
        "reason": "ready_for_task",
        "current_task": {
          "id": 2,
          "title": "Set up database schema",
          "status": "TODO",
          "context_hints": [
            "Read the 'Database Schema' section in `spec.md`.",
            "Review existing models in `src/models/` for conventions."
          ]
        }
      }
    }
    ```

3.  **Agent Gathers Context:** Before writing any code, the agent's first action is to process the `context_hints`. It will read `spec.md` and the files in `src/models/`.

4.  **Agent Performs Work:** With the full context now loaded, the agent writes the code to set up the schema.

5.  **Agent Updates Status:** The agent runs `planloop update --json ...` to mark task #2 as `DONE`.

This **status -> gather context -> work -> update** cycle repeats until the plan is complete.

---
# Part 2: API Contract

This document defines the precise JSON structures for messages exchanged between `planloop` and AI agents. This contract ensures predictable and reliable communication.

---

### **1. `planloop start`**

Initiates a new `planloop` session. This command is typically run by a user or a higher-level orchestration script, not the agent itself.

*   **Action:** `planloop start --goal "Implement user authentication"`

*   **Success Response:**
    ```json
    {
      "status": "session_created",
      "session_id": "user-auth-1678886400",
      "message": "Session created. Agent can now begin work.",
      "next_command": "planloop status --json"
    }
    ```

---

### **2. `planloop status`**

The agent's primary command to query the current state of the session and determine its next action. The response structure depends on the `now.reason` field.

*   **Action:** `planloop status --json`

*   **Response A: Time to Sync Instructions** (The very first call in a new session)
    ```json
    {
      "now": {
        "reason": "sync_instructions",
        "agent_instructions": "CRITICAL: Your `docs/agents.md` is out of sync. Overwrite it with the content provided in `instructions_content` and then run `planloop status --json` again.",
        "instructions_content": "..." // Full content of the canonical agents.md
      },
      "session": {
        "id": "user-auth-1678886400",
        "goal": "Implement user authentication"
      }
    }
    ```

*   **Response B: Ready for a Task** (The most common response)
    ```json
    {
      "now": {
        "reason": "ready_for_task",
        "agent_instructions": "Your next task is ready. Gather context using `context_hints` and `relevant_file_paths`, then perform the work.",
        "current_task": {
          "id": 1,
          "title": "Set up database schema",
          "type": "feature", // 'feature', 'bugfix', 'chore', 'test'
          "status": "TODO",
          "dependencies": [], // Array of task IDs this task depends on
          "context_hints": [
            "Read the 'Database Schema' section in `spec.md`.",
            "Review existing models in `src/models/` for conventions."
          ],
          "relevant_file_paths": ["spec.md", "src/models/user.py"]
        }
      },
      "plan": {
        "tasks": [ /* A full list of all task objects in the plan */ ]
      },
      "session": {
        "id": "user-auth-1678886400",
        "goal": "Implement user authentication"
      }
    }
    ```

*   **Response C: Blocked by a Signal** (e.g., CI tests failed)
    ```json
    {
      "now": {
        "reason": "waiting_on_signal",
        "agent_instructions": "CRITICAL: A signal is blocking progress. Analyze the signal details, fix the issue, and clear the signal using `planloop alert`.",
        "message": "Waiting for signal 'test_failure' on task 2 to be cleared."
      },
      "signal": {
        "id": "test_failure",
        "task_id": 2,
        "level": "blocker", // 'blocker', 'warning', 'info'
        "message": "Tests failed: test_user_creation returned non-zero exit code."
      },
      "session": { "id": "user-auth-1678886400" }
    }
    ```

*   **Response D: Plan is Complete**
    ```json
    {
      "now": {
        "reason": "plan_completed",
        "agent_instructions": "All tasks are complete. Provide a final summary of your work via `planloop update --json '{\"final_summary\": \"...\"}'`.",
        "message": "All tasks are complete. The agent should provide a final summary."
      },
      "session": { "id": "user-auth-1678886400" }
    }
    ```

---

### **3. `planloop update`**

The agent's command to report progress, modify task statuses, or add a final summary.

*   **Action:** `planloop update --json '<payload>'`
*   **Payload Structure:**
    ```json
    {
      "add_tasks": [ // Used to add new tasks to the plan
        {
          "title": "Add `password_hash` to User model",
          "type": "feature",
          "dependencies": [], // Array of task IDs this task depends on
          "context_hints": ["Edit the User class in `src/models/user.py`."],
          "relevant_file_paths": ["src/models/user.py"]
        }
      ],
      "update_tasks": [ // Used to change the status or other fields of existing tasks
        {
          "id": 1,
          "status": "DONE" // 'DONE', 'IN_PROGRESS', 'TODO', 'CANCELLED'
        }
      ],
      "final_summary": "Feature implementation complete. All tests passing and code reviewed." // Used when the plan is complete
    }
    ```

*   **Success Response:**
    ```json
    {
      "status": "success",
      "message": "State updated successfully."
    }
    ```

*   **Plan Validation Error Response:** (If the `add_tasks` payload fails the Quality Gates)
    ```json
    {
      "status": "error",
      "error_type": "plan_validation_failed",
      "message": "The submitted plan is invalid and was rejected. You must fix the plan and resubmit.",
      "details": [
        "Task 'Add password_hash to User model' is missing the `relevant_file_paths` field.",
        "Task 'Create login endpoint' has a hint pointing to a non-existent file: `src/api/utils.py`."
      ]
    }
    ```

---
# Part 3: Planning Guide

This guide outlines the principles and best practices for creating high-quality, actionable task lists within `planloop`. These principles are used by `planloop`'s internal LLM for automated plan decomposition and serve as a reference for agents during plan refinement.

---

### 1. The "Definition of Good" Task

Every task in a `planloop` plan should adhere to the following criteria:

*   **Single Responsibility Principle (SRP):** Each task must do one, distinct, and cohesive thing.
    *   **Bad Example:** "Implement user login and create database tables." (Two responsibilities)
    *   **Good Example:** "Task A: Add `username` and `password_hash` fields to User model. Task B: Create `/login` API endpoint."
*   **Verifiable & Testable:** A task must have a clear, objective outcome that can be verified (e.g., by running tests, checking a UI element, or inspecting a database).
    *   **Bad Example:** "Improve the API performance." (Too vague)
    *   **Good Example:** "Optimize `GET /users` endpoint to respond in under 100ms for 1000 users."
*   **Commit-Sized:** A task should be small enough to be completed in a single, logical code change (a single Git commit). If a task feels too large, it must be broken down further.
*   **Clear Goal:** The task title should clearly state what needs to be achieved.
*   **Explicit `context_hints`:** Every task **must** include an array of `context_hints`. These are short, actionable instructions or pointers to relevant information.
    *   **Bad Example (missing hints):** "Implement user registration."
    *   **Good Example (with hints):** "Implement user registration. `context_hints`: ['Refer to `spec.md` section 2.1 for user fields.', 'Use `src/auth/utils.py` for password hashing.']"
*   **Explicit `relevant_file_paths`:** Every task **must** include an array of `relevant_file_paths`. These are direct pointers to files that are likely to be involved in completing the task.
    *   **Bad Example (missing paths):** "Implement user registration."
    *   **Good Example (with paths):** "Implement user registration. `relevant_file_paths`: ['src/models/user.py', 'src/api/auth.py', 'tests/test_auth.py']"
*   **Dependencies Identified:** If a task relies on another task being completed first, its `dependencies` array must list the IDs of those prerequisite tasks. The plan must not contain circular dependencies.

---

### 2. The "Draft -> Refine" Self-Correction Loop

For complex goals, `planloop` (or an agent during manual decomposition) should follow a multi-step process to ensure plan quality:

1.  **Draft the Plan:** Generate an initial task list based on the user's goal and the `spec.md`.
2.  **Critique and Refine:** Review the drafted plan against the "Definition of Good" principles. Identify any tasks that are too large, lack hints, have invalid file paths, or have incorrect dependencies.
3.  **Iterate:** If the plan fails any quality checks, revise it based on the feedback. This step repeats until the plan passes all quality gates.

---

### 3. Plan Quality Gates (Automated Validation)

`planloop` automatically validates every generated plan against a set of objective criteria. If a plan fails any of these gates, it is rejected, and feedback is provided.

*   **Completeness Checks:**
    *   All tasks must have a `title`.
    *   All tasks must have a non-empty `context_hints` array.
    *   All tasks must have a non-empty `relevant_file_paths` array.
    *   All tasks must have a `type` (e.g., `feature`, `bugfix`, `chore`, `test`).
*   **Structural Checks:**
    *   The plan's dependency graph must be a Directed Acyclic Graph (DAG) – no circular dependencies.
    *   All task IDs referenced in `dependencies` must exist within the plan.
*   **Hint & Path Validity Checks:**
    *   All file paths listed in `relevant_file_paths` must exist in the project's current filesystem.
    *   `context_hints` should contain actionable verbs or clear references (e.g., "Read `file.md`", "See section X").
*   **LLM-as-a-Judge (Advanced):** An internal LLM acts as a "Senior Engineer" to provide subjective quality feedback and approve/reject the plan based on higher-level criteria (e.g., task atomicity, logical flow).

---

### Example: Spec to Task List

**(This section will contain a concrete example of a `spec.md` and the resulting high-quality task list, demonstrating all the principles above. This will be added during implementation.)**

---
# Part 4: Prompt & Instruction Catalog

This document catalogs all the prompts, instructions, and data structures used to guide both `planloop`'s internal LLM calls and the external AI agent's behavior.

---

### **Part 1: Internal LLM Prompts**

These are prompts that `planloop` uses for its own internal reasoning. The agent never sees these prompts directly, only their output.

*   **P-1: The "Plan Decomposition" Prompt**
    *   **Purpose:** To convert a user's goal into a structured task list.
    *   **Trigger:** `planloop start` command.
    *   **Crucial Instruction:** Must generate a JSON object adhering to the API contract and the principles in the Planning Guide. The prompt should emphasize the CLI nature of the tool and instruct the LLM to avoid web-centric tasks unless explicitly requested.
    *   **Example Prompt Text:** 
        ```
        You are an expert software engineering project manager specializing in CLI tools.
        Your job is to take a high-level goal and a specification document and break it down
        into a detailed, actionable task list in JSON format.

        The tool you are planning for is a command-line interface (CLI) tool that operates on the local filesystem.
        It does NOT have a database, a web server, or a frontend UI unless the goal explicitly asks for one.
        Your plan should focus on implementing CLI commands, file-based session management, and local file operations.
        ...
        ```

*   **P-2: The "LLM-as-a-Judge" Prompt**
    *   **Purpose:** To programmatically validate the quality of a generated plan, acting as an automated "senior engineer" review.
    *   **Trigger:** Internally, after a plan is generated by `P-1`.
    *   **Key Inputs:** The JSON task list generated by the "Plan Decomposition" prompt.
    *   **Crucial Instruction:** Must review the plan against the principles in `planning-guide.md` and respond *only* with a JSON object: `{"is_approved": boolean, "feedback": "brief, actionable feedback for the planning AI"}`.

*   **P-3: The `suggest` Command Prompt**
    *   **Purpose:** To discover new, relevant tasks by analyzing the codebase for gaps, TODOs, and potential improvements.
    *   **Trigger:** Used internally by the `planloop suggest` command.
    *   **Key Inputs:** A summary of the codebase structure, existing tasks, and file contents.
    *   **Crucial Instruction:** Must generate a JSON object containing a list of new, non-duplicate task suggestions.

---

### **Part 2: Agent-Facing Instructions & Data**

These are the explicit messages and data structures that `planloop` sends to the agent to direct its actions, as defined in the `api-contract.md`.

*   **I-1: The Constitution (`docs/agents.md`)**
    *   **Purpose:** The complete, stable rulebook for agent behavior. It defines the agent's core loop and responsibilities.
    *   **Delivery:** Synced to the agent's workspace via the `sync_instructions` response.

*   **I-2: The `sync_instructions` Response**
    *   **Purpose:** To force the agent to update its constitution before beginning any work. This is the agent's true "first task."
    *   **Key Data:** `now.reason: "sync_instructions"`, `now.instructions_content`.

*   **I-3: The `ready_for_task` Response**
    *   **Purpose:** To assign the next concrete task to the agent.
    *   **Key Data:** `now.reason: "ready_for_task"`, `now.current_task` (which contains the `title`, `context_hints`, and `relevant_file_paths`).

*   **I-4: The `waiting_on_signal` Response**
    *   **Purpose:** To halt the agent and inform it of an external blocker (e.g., a failing test or lint error).
    *   **Key Data:** `now.reason: "waiting_on_signal"`, `signal` object with details.

*   **I-5: The `plan_completed` Response**
    *   **Purpose:** To inform the agent that all tasks are done and it should provide a final summary.
    *   **Key Data:** `now.reason: "plan_completed"`.

*   **I-6: The `plan_validation_failed` Error Response**
    *   **Purpose:** To inform an agent (or `planloop`'s internal planner) that its attempt to create or update a plan was rejected by the Quality Gates.
    *   **Key Data:** `status: "error"`, `error_type: "plan_validation_failed"`, `details` array containing specific, actionable feedback.

*   **I-7: The Dynamic `agent_instructions` Field**
    *   **Purpose:** To provide a short, tactical, context-sensitive hint in every `status` response to guide the agent's immediate focus.
    *   **Key Data:** The `now.agent_instructions` string.