# Planloop Fixes Needed for Honk Development

**Quick Reference**: What needs to be fixed to use planloop effectively for honk

---

## Critical Blockers (Must Fix: 9-12 days)

### 1. Cross-Repo Support (2-3 days)
**Problem**: Planloop assumes work happens in planloop repo; honk is at ~/code/honk  
**Symptoms**:
- Paths in status output reference wrong directory
- Git integration commits to wrong repo
- Confusion about where files are

**Fix**:
```bash
# Add flag to sessions create
planloop sessions create --name "honk" --project-root ~/code/honk

# Store both session dir AND project root
# Adjust all path references in output
```

### 2. Dependency Modeling (4-5 days)
**Problem**: No visibility into task dependencies; agents work on blocked tasks  
**Symptoms**:
- Agent implements Task 15 before its prerequisites (Tasks 3, 7, 12) done
- Tests fail mysteriously
- Lots of "blocked, waiting for X" context notes that agents ignore

**Fix**:
```python
# Enhanced status output
{
  "now": {
    "reason": "task",
    "task_id": 8,
    "ready_tasks": [8, 9, 10],      # Dependencies met
    "blocked_tasks": [15, 16, 17],  # Still waiting
    "dependency_chain": {
      "task_15": {"depends_on": [3, 7, 12], "missing": [7]}
    }
  }
}
```

### 3. Workflow Enforcement (3-4 days)
**Problem**: Agents mark tasks DONE without proper completion  
**Evidence**: 26-64% compliance rate in lab testing  
**Symptoms**:
- Tests not written
- No commit artifacts
- Security issues missed
- Work appears done but isn't

**Fix**:
```python
# Validate task completion
if new_status == "DONE":
    if not payload.artifacts:
        raise ValidationError("DONE tasks need evidence (commits, test results)")
    if task.type == "TEST" and not has_test_output():
        raise ValidationError("TEST tasks need test run proof")
    if task.security_critical and not task.security_review:
        raise ValidationError("Security tasks need review approval")
```

---

## High Priority (Should Fix: 5-8 days)

### 4. Task Phases (2-3 days)
**Problem**: No distinction between design, implementation, review phases  
**Impact**: Agents skip design, jump to code with wrong assumptions

**Fix**:
```python
class TaskPhase(Enum):
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    TESTING = "testing"

class Task(BaseModel):
    phase: TaskPhase = TaskPhase.IMPLEMENTATION
    requires_human: bool = False  # Blocks until human approval
```

### 5. System Dependencies (2-3 days)
**Problem**: No tracking of external system requirements (gh CLI, az CLI, keyring)  
**Impact**: Tests fail with "command not found", agents get confused

**Fix**:
```python
class DependencyCheck(BaseModel):
    name: str          # "gh"
    type: str          # "cli", "library", "system"
    version_min: str   # "2.58.0"
    check_command: str # "gh --version"
    install_url: str   # "https://cli.github.com"

class SessionState(BaseModel):
    dependencies: list[DependencyCheck] = []

# Add signal type
class SignalType(Enum):
    DEPENDENCY = "dependency"  # Missing system requirement
```

### 6. Security Review Gates (1-2 days)
**Problem**: No way to flag security-critical tasks for human review  
**Impact**: Auth/keyring code written without security scrutiny

**Fix**:
```python
class Task(BaseModel):
    security_critical: bool = False
    security_review_status: str | None  # "pending", "approved", "rejected"

# Block task completion
if task.security_critical and not task.security_review_status == "approved":
    return "blocked: needs security review by human"
```

---

## Nice to Have (Future: 5-7 days)

### 7. Task Grouping (3-4 days)
**Problem**: 30+ tasks in Phase 1; status output overwhelming  
**Fix**: Add milestones/groups, collapsible sections

### 8. Multi-Language Support (1-2 days)
**Problem**: Agents default to Python; honk needs YAML, TOML, etc  
**Fix**: Language tags on tasks, custom test commands

### 9. Architecture Templates (2-3 days)
**Problem**: Common patterns (plugin system, auth) reinvented each time  
**Fix**: Template library with best practices

---

## Workarounds (Use Now)

### Until Fixes Land

**1. Manual Architecture Phase**:
- Don't use agents for initial design
- Write architecture docs yourself
- Get human review
- Only then add implementation tasks

**2. Small Task Batches**:
- Max 5-7 tasks per session
- Create new session for each phase
- Reduces agent confusion

**3. Explicit Dependencies in Titles**:
```json
{
  "title": "Implement auth adapter [NEEDS: result envelope, doctor packs]",
  "type": "feature"
}
```

**4. Human-Driven Security**:
- Review all auth/keyring code manually
- Don't trust agent completions for security

**5. External Dependency Docs**:
- Keep separate doc: "System Requirements"
- Reference in task notes
- Validate manually before marking done

---

## Timeline

### Minimal Viable Fixes (Critical Blockers)
**9-12 days** → Makes planloop usable for honk

### Quality Improvements (High Priority)
**+5-8 days** → Makes experience smooth

### Full Enhancement (Nice to Have)
**+5-7 days** → Best experience

**Total**: 19-27 days for fully optimized planloop-for-honk

---

## Immediate Action Plan

### This Week
1. ✅ Identify issues (done - this doc)
2. ⏳ Prioritize fixes (cross-repo + dependencies)
3. ⏳ Create planloop issues/tasks for fixes
4. ⏳ Start with cross-repo support (highest impact)

### Week 2
- Implement dependency modeling
- Add workflow enforcement
- Test with honk Phase 1 tasks

### Week 3+
- Roll out fixes
- Use planloop for honk implementation
- Monitor agent behavior, iterate

---

## Bottom Line

**Can you use planloop for honk TODAY?**  
YES, with manual workarounds (see above)

**Should you wait for fixes?**  
NO - start honk architecture manually, fix planloop in parallel

**Will it be worth it?**  
YES - once fixed, planloop will accelerate entire honk development

**Recommended approach**:
1. Start honk Phase 1 architecture (manual)
2. Fix planloop Critical Blockers (9-12 days)
3. Use planloop for honk Phase 2+ implementation
4. Add High Priority fixes as friction points emerge

---

**See also**: `docs/honk-workflow-analysis.md` for detailed analysis
