# Using Planloop to Build Honk: Real Workflow Analysis

**Date**: 2025-11-18  
**Context**: You want to use planloop to MANAGE the development of honk (not as code foundation)  
**Time Investment**: Deep thinking about actual workflow friction

---

## Executive Summary

Using planloop to manage honk's development is **viable but will expose several workflow gaps**. The good news: most are fixable. The key insight is that **honk's architecture requires different task granularity** than typical feature development.

**Main Issues to Fix**:
1. **Task granularity mismatch** - Honk needs architectural/design tasks that planloop doesn't handle well
2. **Cross-repo coordination** - Planloop expects single repo; honk development happens elsewhere
3. **Dependency modeling** - Complex prerequisites (doctor packs before auth before demo) need better support
4. **Agent behavior** - Current 26-64% compliance means agents will skip critical steps
5. **System integration** - No way to track external dependencies (gh CLI, az CLI, keyring)

**But these are solvable.** Let me break down the real issues...

---

## Part 1: The Actual Workflow You'll Experience

### Scenario: Week 1 of Honk Development

**You want to do**:
```bash
cd ~/code/honk
planloop sessions create --name "honk-bootstrap"
# Add tasks for Phase 1: Environment setup
```

**What happens**:

1. ✅ Session creation works fine
2. ✅ You can add tasks via update payload
3. ❌ **Problem 1**: Task list becomes unwieldy quickly

Let me show you why...

---

## Part 2: Task Granularity Mismatch (CRITICAL ISSUE)

### Honk Phase 1 Needs ~25-30 Tasks

**Environment Setup** (5 tasks):
- Create repo structure
- Set up uv with Python 3.12.2  
- Add locked dependencies
- Create noxfile.py with sessions
- Set up pre-commit hooks

**Result Envelope System** (6-8 tasks):
- Design ResultEnvelope Pydantic model
- Implement result.ok() helper
- Implement result.error() helper
- Implement result.prereq_failed() helper
- Commit schemas/result.v1.json
- Add CI validation step
- Create decorator for command wrapping
- Write envelope tests

**Plugin Registry** (7-9 tasks):
- Design area metadata model
- Implement entry point scanner
- Create dynamic area loader
- Add error handling
- Write registry tests
- Document plugin system
- Create example area plugin

### Planloop's Current Limitations

**Problem**: Agents struggle with >10 tasks:
- Status output becomes overwhelming
- Dependency chains get confusing
- Agents lose track of architectural decisions
- No way to group related tasks

**Evidence from metrics**:
- OpenAI: 5.3% pass rate, "missing update" is #2 error
- Claude: 46% pass rate, "missing status-after" is #1 error
- Even Copilot at 58% misses workflow steps

**What this means for honk**:
You'll need to break Phase 1 into multiple planloop sessions or agents will:
- Skip architectural design tasks
- Implement parts out of order
- Forget to write tests
- Miss CI setup

---

## Part 3: Cross-Repo Coordination (MEDIUM ISSUE)

### The Setup

**Planloop session** exists at `~/.planloop/sessions/<id>/`  
**Honk development** happens at `~/code/honk/`

**Current behavior**:
```bash
cd ~/code/honk
export PLANLOOP_SESSION=<id>
planloop status --json
# Works, but...
```

**Issues**:

1. **Project root mismatch**: Session stores `project_root: /Users/honk/code/planloop`
   - This is WHERE you ran planloop from
   - Not where honk development happens
   - Status output references wrong paths

2. **Git integration broken**: 
   - `planloop snapshot` commits to planloop's .git, not honk's
   - Artifacts reference wrong repo
   - Branch tracking doesn't work

3. **File path confusion**:
   - Agents see relative paths from planloop repo
   - Tasks reference files that don't exist there
   - Constant path translation needed

### Fix Required

**Option A**: Add `--project-root` flag to sessions create:
```bash
planloop sessions create --name "honk-bootstrap" --project-root ~/code/honk
```

**Option B**: Make planloop "project-aware":
- Detect git repo from cwd
- Store both planloop session dir AND project root
- Adjust all path references accordingly

**Effort**: 2-3 days to implement properly

---

## Part 4: Dependency Modeling (HIGH PRIORITY)

### Honk's Complex Prerequisites

**Real dependency chain**:
```
Environment setup
    ↓
Result envelope system ← Plugin registry needs this
    ↓         ↓
Doctor packs  Plugin registry
    ↓         ↓
Auth subsystem ← Needs both doctor + plugins
    ↓
Demo command ← Needs ALL of the above
```

**Planloop's current support**:
```python
class AddTaskInput(BaseModel):
    depends_on: list[PositiveInt]  # Just task IDs
```

**What's missing**:

1. **No dependency reasoning**:
   - Agents can't see "Task 15 needs Task 3, 7, 12 done first"
   - Status doesn't show blocked tasks clearly
   - No "ready to work" vs "blocked" distinction

2. **No architectural dependencies**:
   - "Design plugin system" must finish before "Implement registry"
   - Design tasks have no special status
   - Agents treat them like regular feature work

3. **No external dependencies**:
   - Doctor packs need `gh` CLI installed
   - Auth subsystem needs `keyring` library
   - No way to represent "system prerequisite not met"

### What Happens Without This

**Week 3 of honk development**:
```
Agent sees: "Task 15: Implement auth GitHub adapter"
Agent thinks: "I can start this now"
Agent implements: Uses result.error() that doesn't exist yet
Agent fails: Tests don't pass, gets confused
Agent loops: Tries to fix, makes it worse
```

**You intervene**:
```bash
# Manually reorder tasks
# Add context notes: "BLOCKED: needs result envelope done first"
# Agent reads notes, ignores them
# Cycle repeats
```

### Fix Required

**Enhance task model**:
```python
class Task(BaseModel):
    id: int
    title: str
    depends_on: list[int]
    blocked_reason: str | None  # "Waiting on task 3, 7"
    requires_system: list[str]  # ["gh>=2.58.0", "keyring"]
    design_phase: bool  # True for architecture tasks
```

**Enhance status output**:
```json
{
  "now": {
    "reason": "task",
    "task_id": 8,
    "ready_tasks": [8, 9, 10],  // Dependencies met
    "blocked_tasks": [15, 16],  // Waiting on others
    "system_checks": {
      "gh": "2.60.0 ✓",
      "keyring": "24.3.1 ✓"
    }
  }
}
```

**Effort**: 4-5 days to implement properly

---

## Part 5: Agent Behavior Issues (CRITICAL)

### Current Performance Reality

**From labs/metrics.json**:
- **OpenAI**: 5.3% pass rate
  - Top errors: "trace log missing" (76%), "missing status-after" (19%), "missing update" (17%)
  - **Translation**: Agent doesn't follow workflow AT ALL
  
- **Claude**: 46% pass rate
  - Top errors: "missing status-after" (47%), "missing update" (46%)
  - **Translation**: Agent skips validation steps
  
- **Copilot**: 58% pass rate (best, but still concerning)
  - Works most of the time, but 42% failure rate means...
  - **Translation**: ~2 out of 5 tasks will have workflow issues

### What This Means for Honk

**The brutal truth**: If agents can't consistently manage 2 simple tasks (hello command + tests), they will struggle with honk's 30-50 task bootstrap.

**Projected issues**:

1. **Architecture tasks skipped**:
   - "Design result envelope schema" → Agent jumps straight to implementation
   - Schema inconsistencies discovered later
   - Refactor required, time wasted

2. **Test coverage gaps**:
   - "Write doctor pack tests" → Agent marks done without full coverage
   - Tests pass locally, fail in CI
   - Debug cycle starts

3. **Security issues**:
   - "Implement keyring storage" → Agent uses env vars instead
   - Security review catches it
   - Complete rewrite required

4. **Integration problems**:
   - "Wire up doctor packs" → Agent forgets to call in commands
   - Commands silently skip prerequisites
   - Bugs in production

### Why This Happens

**Looking at trace logs**:
```
Agent: status → sees task → implements → commits
Missing: status AFTER to verify → moves to next task
Result: No validation that task actually complete
```

**Root cause**: Agents optimize for "task done fast" not "task done correctly"

### Fixes Required

**1. Stricter workflow enforcement** (3-4 days):
```python
# In planloop update validation
def validate_task_completion(task_id, prev_status, new_status):
    if new_status == "DONE":
        # Require evidence
        if not payload.artifacts:
            raise ValidationError("DONE tasks need artifacts (commits, test results)")
        if task.type == "TEST" and not has_test_output():
            raise ValidationError("TEST tasks need test run evidence")
```

**2. Task completion checklist** (2-3 days):
```python
class Task(BaseModel):
    checklist: list[CheckItem] = []  # Auto-generated based on type

# For type=FEATURE:
checklist = [
    CheckItem(text="Tests written", required=True),
    CheckItem(text="Tests passing", required=True),
    CheckItem(text="Code reviewed", required=False),
]
```

**3. Better agent instructions** (ongoing):
- Emphasize: "DONE means fully complete, not just working"
- Add examples of good vs bad task completion
- Highlight common mistakes

---

## Part 6: System Integration Gaps (MEDIUM-HIGH)

### Honk Requires External Systems

**Phase 2-3 dependencies**:
- `gh` CLI ≥ 2.58.0 for GitHub auth
- `az` CLI ≥ 2.63.0 for Azure DevOps
- `keyring` library for macOS Keychain
- Xcode (macOS only) for runner tools
- Node.js 20.13.1 (optional, for web UI)

**Planloop has no concept of this**.

**Current signals**:
```python
class SignalType(Enum):
    CI = "ci"           # GitHub Actions failure
    LINT = "lint"       # Ruff/mypy issues
    BENCH = "bench"     # Performance regression
    SYSTEM = "system"   # Generic system issue
    OTHER = "other"
```

**What's missing**: **DEPENDENCY signal type**

### What Happens Without This

**Week 4 scenario**:
```
Task: "Implement GitHub auth adapter"
Agent: Writes code calling gh CLI
Agent: Runs tests
Tests: FAIL - gh command not found
Agent: Confused, tries to fix code
Agent: Still failing
You: "Install gh CLI first!"
Agent: Oh. *installs gh*
Agent: Tests pass now
But: No record this was a dependency issue
Next agent: Same problem repeats
```

### Fix Required

**1. Add dependency tracking** (2-3 days):
```python
class DependencyCheck(BaseModel):
    name: str          # "gh"
    type: str          # "cli", "library", "system"
    version_min: str   # "2.58.0"
    check_command: str # "gh --version"
    install_url: str   # "https://cli.github.com"
    required_for: list[int]  # Task IDs

class SessionState(BaseModel):
    dependencies: list[DependencyCheck] = []
```

**2. Dependency validation in workflow** (1-2 days):
```bash
# Before task starts
planloop check-deps --task-id 15
# Output: "Task 15 needs: gh>=2.58.0 (missing), keyring>=24.3.1 (ok)"
# Blocks task start until resolved
```

**3. Better signal for dep issues** (1 day):
```python
planloop alert --open --type dependency \
  --title "Missing gh CLI" \
  --message "Install gh>=2.58.0 from https://cli.github.com"
```

---

## Part 7: Specific Honk Challenges

### Challenge 1: Plugin System Design

**Nature**: Pure architecture, no code yet  
**Task breakdown**:
1. Research entry point patterns
2. Design area metadata schema
3. Design plugin discovery flow
4. Document plugin contract
5. Get review/approval
6. Begin implementation

**Problem**: Tasks 1-4 are DESIGN, task 5 is HUMAN-REQUIRED, task 6 is CODE

**Planloop doesn't distinguish these**.

**What happens**:
- Agent sees task 1: "Research entry point patterns"
- Agent writes code immediately (skips research)
- Code is based on wrong assumptions
- Later refactor required

**Fix needed**: 
```python
class TaskPhase(Enum):
    DESIGN = "design"      # Human reviews before implementation
    IMPLEMENTATION = "implementation"  # Agent can do
    REVIEW = "review"      # Human approval gate
    TESTING = "testing"    # Agent validates

class Task(BaseModel):
    phase: TaskPhase = TaskPhase.IMPLEMENTATION
    requires_human: bool = False  # Blocks until human marks "approved"
```

**Effort**: 2-3 days

---

### Challenge 2: Security-Critical Code

**Honk has**:
- Auth token storage (keyring integration)
- PAT rotation flows
- Credential validation
- Secret redaction

**Planloop has no concept of "security review required"**.

**What happens**:
```
Task: "Implement keyring token storage"
Agent: Writes code using env vars (easier)
Agent: Tests pass
Agent: Marks done
Later: Security review finds issue
Result: Complete rewrite needed
```

**Fix needed**:
```python
class Task(BaseModel):
    security_critical: bool = False
    security_review_status: str | None  # "pending", "approved", "rejected"

# In workflow
if task.security_critical and not task.security_review_status:
    return "blocked: needs security review"
```

**Effort**: 1-2 days

---

### Challenge 3: Multi-Language Support

**Honk eventually needs**:
- Python (core CLI)
- Nox (task automation)
- GitHub Actions YAML (CI)
- TOML (config files)
- Optional: TypeScript/React (web UI)

**Planloop is Python-focused**.

**Issues**:
- Agents default to Python solutions
- No way to specify "this task is YAML"
- No cross-language dependency tracking
- Test commands are Python-centric

**Fix needed**: 
```python
class Task(BaseModel):
    languages: list[str] = ["python"]  # Can be multiple
    test_command: str | None  # Custom per task

# Status output
if task.languages != ["python"]:
    print(f"Note: Task involves {', '.join(task.languages)}")
```

**Effort**: 1-2 days

---

## Part 8: What Actually Works Well

### Planloop's Strengths for Honk

**1. Task tracking is solid** ✅
- Task model is flexible enough
- Status/update loop is clear
- Locking prevents conflicts

**2. Signal system is great for CI** ✅
- GitHub Actions failures → open signal
- Agent handles signal → closes signal
- This maps perfectly to honk's CI needs

**3. TDD workflow fits** ✅
- "Write tests" → "Implement" → "Refactor" flow
- Matches honk's spec requirements
- Agent instructions emphasize tests-first

**4. Context notes are helpful** ✅
- Can store architectural decisions
- Agents *sometimes* read them
- Better than nothing

**5. Lab testing catches issues** ✅
- Real agent testing shows problems early
- Can run honk-specific scenarios
- Metrics track improvement

### What You Can Do Today

**Use planloop for**:
- Implementation tasks (once architecture decided)
- Test writing
- Bug fixing
- CI maintenance
- Documentation

**Don't use planloop for**:
- Initial architecture design (do this manually)
- Security-critical code (human review first)
- Complex cross-system integration (needs more tooling)

---

## Part 9: Prioritized Fix List

### Must Fix (Blocks honk development)

**1. Cross-repo support** (2-3 days)
- Add --project-root to sessions
- Fix path handling
- Update status output

**2. Dependency modeling** (4-5 days)
- Add depends_on reasoning to status
- Show blocked vs ready tasks
- Add system dependency checks

**3. Agent workflow enforcement** (3-4 days)
- Require artifacts for DONE tasks
- Add task completion checklists
- Better validation

**Total**: 9-12 days to make planloop viable for honk

---

### Should Fix (Quality of life)

**4. Task phases** (2-3 days)
- Design vs implementation vs review
- Human approval gates
- Security review flags

**5. System integration** (2-3 days)
- Dependency signal type
- External CLI tracking
- Better install guidance

**6. Multi-language hints** (1-2 days)
- Language tags on tasks
- Custom test commands
- Cross-language awareness

**Total**: 5-8 days for better experience

---

### Nice to Have (Future)

**7. Task grouping** (3-4 days)
- Phases or milestones
- Collapsible in status output
- Better overview

**8. Architecture templates** (2-3 days)
- Common patterns (plugin system, auth, etc)
- Generate task skeletons
- Best practices built-in

**9. Better agent guidance** (ongoing)
- Task-specific instructions
- Common mistake warnings
- Success criteria examples

---

## Part 10: Concrete Recommendations

### For Implementing Honk This Week

**Setup** (Do now):
```bash
# 1. Create honk repo
cd ~/code && mkdir honk && cd honk
git init
uv init --name honk --python 3.12

# 2. Create planloop session
export PLANLOOP_HOME=~/.planloop-honk  # Separate from main
planloop sessions create --name "honk-phase1"

# 3. Add ONLY Phase 1 architecture tasks (5-7 tasks max)
cat > tasks.json << 'EOF'
{
  "session": "<id>",
  "add_tasks": [
    {"title": "Research + document plugin system patterns", "type": "design"},
    {"title": "Design result envelope schema", "type": "design"},
    {"title": "Design doctor pack architecture", "type": "design"},
    {"title": "Get architecture review approval", "type": "doc"},
    {"title": "Set up repo structure", "type": "chore"}
  ]
}
EOF
planloop update --file tasks.json
```

**Work manually on architecture** (Week 1):
- Don't use agents for design decisions
- Write architecture docs yourself
- Get human review
- Once approved, THEN add implementation tasks

**Add implementation tasks** (Week 2):
```bash
# After architecture approved
# Add 5-10 implementation tasks
# Use agents for these
planloop suggest  # Let AI suggest concrete implementation tasks
```

**Use agents for**:
- Implementing designed systems
- Writing tests
- Fixing bugs
- Refactoring code

**Don't use agents for**:
- Initial architecture decisions
- Security-critical code (review required)
- Complex integration (too error-prone)

---

### For Fixing Planloop

**Priority 1**: Cross-repo support
```bash
# Add to planloop CLI
planloop sessions create --name "honk" --project-root ~/code/honk
# Stores both session dir and project root
# All operations respect project root
```

**Priority 2**: Better dependency handling
```bash
# Add to status output
{
  "now": {
    "reason": "task",
    "task_id": 8,
    "ready_tasks": [8, 9],      # Can start now
    "blocked_tasks": [15, 16],  # Waiting on deps
    "dependencies": {
      "task_8": [],
      "task_15": [3, 7, 12]     # Blocked by these
    }
  }
}
```

**Priority 3**: Workflow enforcement
```python
# Add validation
if task.status == "DONE":
    if not task.artifacts:
        raise ValidationError("DONE tasks need evidence")
    if task.type == "TEST" and not has_test_results():
        raise ValidationError("TEST tasks need passing tests")
```

---

## Conclusion

### Can You Use Planloop for Honk? **YES, WITH FIXES**

**Timeline**:
- **Week 0** (now): Manual architecture work, planloop tracks tasks loosely
- **Week 1-2**: Fix cross-repo + dependencies in planloop (9-12 days)
- **Week 3+**: Use planloop properly for implementation phase

**Realistic expectations**:
- Agents will make mistakes (current 26-64% compliance)
- You'll need to supervise and correct
- Works better for implementation than architecture
- Invest in fixes now, benefit for months

**Alternative**:
- Use planloop as-is for tracking, do work manually
- Wait for fixes before relying on agents heavily
- Hybrid: planloop tracks, humans implement critical parts

**My recommendation**: 
Fix cross-repo + dependency support (Priority 1-2, ~7-9 days), then use planloop to manage honk implementation. The time investment pays off across the entire project.

---

**Generated**: 2025-11-18  
**Analysis type**: Realistic workflow simulation  
**Based on**: Actual agent performance data + honk spec requirements  
**Actionable**: Yes - concrete fixes + workarounds provided
