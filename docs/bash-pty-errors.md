# Bash Tool / PTY Errors - Comprehensive Analysis

**Last Updated**: 2025-11-18  
**Status**: ACTIVE ISSUE - Workarounds documented

---

## Executive Summary

The GitHub Copilot CLI bash tool experiences intermittent `posix_spawnp failed` errors during long-running agent sessions. This is a **terminal/PTY corruption issue**, not a planloop bug. The error blocks all bash command execution and requires session resets to recover.

**Impact**: CRITICAL - Breaks agent workflow mid-session  
**Frequency**: Occurs after ~30-50 bash commands in a single session  
**Root Cause**: PTY/process resource exhaustion in Copilot CLI bash tool  
**Fix Status**: No upstream fix available - requires workarounds

---

## Error Manifestations

### Primary Error
```
<exited with error: posix_spawnp failed.>
```

**What This Means**:
- The underlying POSIX process spawning system call failed
- The bash session's PTY (pseudo-terminal) is corrupted
- No new processes can be spawned in that session
- The session is unrecoverable

### Secondary Symptoms
- Commands that previously worked suddenly fail
- No output from bash commands (silent failures)
- Error persists across different command types
- Switching to explicit Python paths doesn't help
- File creation with `create` tool still works (no bash needed)

---

## Observed Patterns

### When It Happens

**Session Longevity**:
- First 20-30 commands: ✅ Works fine
- Commands 30-50: ⚠️ Increased risk
- Beyond 50 commands: ❌ High probability of failure

**Command Complexity**:
- Simple commands (`ls`, `cat`): Less likely to trigger
- Complex chains (`cd && source && python`): More likely
- Long-running commands (pytest, git operations): Higher risk

**Resource Indicators**:
- Many subprocess spawns
- Heavy environment variable usage
- Multiple directory changes
- File descriptor accumulation

### Recovery Patterns

**What DOESN'T Work**:
- ❌ Retrying the same command
- ❌ Using different bash syntax
- ❌ Switching to explicit paths
- ❌ Sourcing virtual environments differently

**What WORKS**:
- ✅ Creating fresh bash session with new `sessionId`
- ✅ Using `create` tool instead of bash for file writes
- ✅ Using explicit `.venv/bin/python` paths
- ✅ Simplifying commands (avoid chains)

---

## Root Cause Analysis

### Technical Details

**PTY Corruption**:
- Copilot CLI bash tool maintains long-lived PTY sessions
- PTY has limited resources (file descriptors, process table entries)
- Long sessions accumulate state that isn't properly cleaned up
- Eventually, `posix_spawnp()` cannot allocate new process context

**Similar Issues**:
- GitHub Issue #185: bash commands not working in Copilot CLI
- VS Code Issue #5997: Copilot agent missing command output
- Common in Node.js-based terminal emulators under heavy load

**Why It's Hard to Fix**:
- Requires upstream changes to Copilot CLI
- Node.js PTY handling is complex
- Difficult to reproduce consistently
- May be macOS/Linux-specific (PTY implementation differs)

---

## Documented Workarounds

### 1. Session Rotation Strategy ⭐ RECOMMENDED

**Approach**: Use fresh bash sessions before corruption occurs

```python
# Bad: Reuse same session
sessionId = "work"
bash(command1, sessionId="work")
bash(command2, sessionId="work")  # ... eventually fails
bash(command50, sessionId="work")  # ❌ posix_spawnp failed

# Good: Rotate sessions
bash(command_group_1, sessionId="session1")
bash(command_group_2, sessionId="session2")
bash(command_group_3, sessionId="session3")
```

**Implementation**:
- Create new `sessionId` every 10-15 commands
- Use descriptive names: `planloop_task1`, `planloop_task2`
- Monitor for errors and rotate proactively

### 2. Explicit Python Paths

**Approach**: Avoid relying on virtual environment activation

```bash
# Bad: Requires sourcing (adds complexity)
source .venv/bin/activate && python -m planloop.cli status

# Good: Direct Python path
.venv/bin/python -m planloop.cli status
```

**Why It Helps**:
- Fewer subprocess spawns
- Simpler command execution
- Reduces PTY state accumulation

### 3. Command Simplification

**Approach**: Break complex chains into smaller steps

```bash
# Bad: Complex chain with many operations
cd /path && source .venv/bin/activate && export VAR=value && python script.py && echo done

# Good: Separate, focused commands
bash("cd /path", sessionId="step1")
bash(".venv/bin/python script.py", sessionId="step2")
```

**Why It Helps**:
- Each command is simpler
- Less likely to trigger PTY issues
- Easier to debug failures

### 4. Alternative Tools

**Approach**: Use non-bash tools when possible

```python
# Instead of: bash("cat file.txt")
view("/path/to/file.txt")

# Instead of: bash("echo 'content' > file.txt")
create("/path/to/file.txt", "content")

# Instead of: bash("grep pattern file")
grep(pattern="pattern", path="/path/to/file")
```

**Why It Helps**:
- Avoids bash entirely
- More reliable
- Better error messages

### 5. Error Detection & Recovery

**Approach**: Detect failures and automatically recover

```python
def safe_bash(command, max_retries=2):
    """Execute bash with automatic session rotation on failure."""
    for attempt in range(max_retries):
        sessionId = f"auto_{attempt}_{time.time()}"
        result = bash(command, sessionId=sessionId)
        
        if "posix_spawnp failed" not in result:
            return result
        
        # Failed, try new session
        print(f"PTY error detected, rotating session (attempt {attempt + 1})")
    
    raise RuntimeError("Bash command failed after retries")
```

---

## Agent-Specific Guidance

### For Long-Running Tasks

When working on multi-task sessions:

1. **Start fresh**: Use new `sessionId` for each major task
2. **Monitor commands**: Track how many bash calls you've made
3. **Rotate proactively**: Don't wait for failure - rotate at ~10 commands
4. **Use alternatives**: Prefer `view`, `create`, `grep` over bash

### For Debugging

When investigating bash failures:

1. **Check command count**: How many bash calls in this session?
2. **Try new session**: Create fresh `sessionId` immediately
3. **Simplify command**: Break into smaller pieces
4. **Use alternatives**: Can this be done without bash?

### Current Session Example

**What Happened** (Session: agent-and-prompt-tooling-20251118T193318Z-8c7f):

- Started working through 7 tasks
- Used same bash session repeatedly
- Around task 5-6, bash started failing with `posix_spawnp failed`
- **Workaround applied**:
  - Created fresh session: `sessionId="planloop_work"`
  - Used explicit Python paths: `.venv/bin/python`
  - Continued successfully through task 7
  - ✅ All tasks completed

---

## Logging & Diagnostics

### Where to Look for Errors

**Copilot CLI Logs** (according to GitHub docs):

**VS Code**:
```
View > Output > Select "GitHub Copilot"
```

**Command Palette**:
```
Developer: Open Extension Logs Folder
```

**JetBrains IDEs**:
```
Help > Show Log in Finder/Explorer
Open: idea.log
```

**Enable Debug Logging** (JetBrains):
```
Help > Diagnostic Tools > Debug Log Settings
Add: #com.github.copilot:trace
```

### What to Capture

When reporting bash/PTY issues:

1. **Command count**: How many bash calls before failure?
2. **Command types**: Simple? Complex? Long-running?
3. **Session duration**: How long had session been running?
4. **Platform details**: macOS/Linux version, shell type
5. **Copilot version**: CLI version number
6. **Error output**: Full error message
7. **Recovery method**: What finally worked?

### Planloop-Specific Logs

**Agent Transcript**:
```bash
# View last 50 agent commands/responses
planloop logs --limit 50 --session <session_id>

# Check for bash errors
planloop logs --session <session_id> | grep "posix_spawnp"
```

**Session Logs**:
```bash
# Location
~/.planloop/sessions/<session_id>/logs/

# Files
- agent-transcript.jsonl  # All agent interactions
- planloop.jsonl          # Structured events
- planloop.log            # Human-readable log
```

---

## Comparison: Similar Issues

### TTY Requirement for `-p` Flag (Related)

**Issue**: Copilot CLI `-p` flag doesn't work in scripted/non-interactive contexts

**Symptoms**:
- No output when using `copilot -p "prompt"` in automation
- Exits with code 1
- No logs created

**Root Cause**: Copilot CLI requires true TTY for `-p` mode

**Workarounds**:
- Use `expect` for TTY emulation
- Pipe to interactive mode instead of `-p`
- Use GitHub CLI's `/session` API (if available)

**References**:
- GitHub Issue #560
- Community Discussion #161238

**Difference from PTY Corruption**:
- TTY issue: Prevents `-p` usage entirely (design limitation)
- PTY corruption: Progressive failure during long sessions (resource bug)

---

## Future Solutions

### Upstream Fixes Needed

**In Copilot CLI** (GitHub's responsibility):

1. **PTY Resource Management**:
   - Implement proper cleanup after each command
   - Monitor file descriptor usage
   - Detect and reset corrupted PTY state
   - Add session health checks

2. **Session Lifecycle**:
   - Add explicit session reset capability
   - Implement automatic session rotation
   - Provide session health metrics

3. **Better Error Messages**:
   - Distinguish PTY errors from command errors
   - Suggest recovery actions
   - Log diagnostic information

4. **Logging Improvements**:
   - Make log location discoverable (`/session` output)
   - Include session health metrics
   - Add PTY state information

### Planloop Mitigations (Can Implement Now)

1. **Automatic Session Rotation**:
   - Detect bash failures
   - Automatically create fresh sessions
   - Track commands per session
   - Rotate before failure occurs

2. **Bash Abstraction Layer**:
   - Wrap bash tool in safe executor
   - Implement retry logic
   - Prefer alternative tools
   - Monitor session health

3. **Agent Guidance**:
   - Document workarounds in agents.md
   - Include in workflow contract
   - Provide recovery examples
   - Train agents on alternatives

4. **Monitoring & Alerts**:
   - Log bash command count per session
   - Alert when approaching limits
   - Track failure patterns
   - Record successful workarounds

---

## References

### GitHub Issues
- [Copilot CLI #185](https://github.com/github/copilot-cli/issues/185): bash commands not working
- [Copilot CLI #520](https://github.com/github/copilot-cli/issues/520): Add log location to `/session`
- [Copilot CLI #560](https://github.com/github/copilot-cli/issues/560): TTY requirement for `-p` flag
- [VS Code #5997](https://github.com/microsoft/vscode-copilot-release/issues/5997): Agent missing command output

### Official Documentation
- [Viewing Copilot Logs](https://docs.github.com/en/copilot/how-tos/troubleshoot-copilot/view-logs)
- [Troubleshooting Copilot](https://docs.github.com/en/copilot/how-tos/troubleshoot-copilot)
- [Tracking Copilot Sessions](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/track-copilot-sessions)

### Planloop Documentation
- `docs/lab-testing.md` (Known Issues section)
- `docs/honk-case-study.md` (Workarounds section)
- `docs/agents.md` (Workflow contract)

### Community Resources
- [GitHub Blog: Copilot CLI Tutorial](https://github.blog/ai-and-ml/github-copilot/github-copilot-cli-how-to-get-started/)
- [Stack Overflow: Copilot Errors](https://stackoverflow.com/questions/68253302/github-copilot-commands-not-working-and-showing-error)
- [HostingSeekers: Copilot Error Fixes](https://www.hostingseekers.com/blog/github-copilot-errors-and-fixes/)

---

## Action Items

### Immediate (This Week)

- [ ] **Document in agents.md**: Add bash error section to workflow contract
- [ ] **Create bash wrapper**: Implement safe_bash() with auto-rotation
- [ ] **Update session feedback**: Track bash command count and report
- [ ] **Add monitoring**: Log bash usage per session

### Short Term (Next Sprint)

- [ ] **Implement auto-rotation**: Detect failures and rotate automatically
- [ ] **Add health checks**: Monitor PTY state and warn before failure
- [ ] **Create recovery guide**: Step-by-step for agents when bash fails
- [ ] **Test thresholds**: Find optimal command count before rotation

### Long Term (Ongoing)

- [ ] **Report to GitHub**: File detailed issue with repro steps
- [ ] **Track upstream fixes**: Monitor Copilot CLI releases
- [ ] **Measure impact**: Track how often workarounds are needed
- [ ] **Refine strategies**: Update based on real-world usage

---

## Appendix: Technical Deep Dive

### POSIX Spawn System Call

`posix_spawnp()` is a system call that creates a new child process:

```c
int posix_spawnp(
    pid_t *pid,              // Output: new process ID
    const char *file,        // Program to execute
    const posix_spawn_file_actions_t *file_actions,
    const posix_spawnattr_t *attrp,
    char *const argv[],      // Arguments
    char *const envp[]       // Environment
);
```

**Failure Modes**:
- `EAGAIN`: Process table full or resource limits hit
- `ENOMEM`: Insufficient memory
- `ENOENT`: Program not found
- **In PTY context**: Often indicates PTY corruption

### PTY Architecture

**How Copilot CLI Bash Works**:

```
[Copilot CLI Agent]
      ↓
[Node.js PTY Library]
      ↓
[Pseudo-Terminal Master] ←→ [Pseudo-Terminal Slave]
      ↓                            ↓
[File Descriptors]            [Bash Process]
      ↓                            ↓
[posix_spawnp()]             [Your Command]
```

**Failure Point**: When PTY master runs out of resources or gets corrupted, `posix_spawnp()` fails to create new child processes.

### Node.js PTY Libraries

Copilot CLI likely uses `node-pty` or similar:
- Wraps OS-level PTY APIs
- Manages terminal sessions
- Handles I/O buffering
- **Known issues**: Resource leaks, corruption under heavy load

---

**Version**: 1.0.0  
**Maintainer**: Planloop Development Team  
**Status**: Living Document - Update as we learn more
