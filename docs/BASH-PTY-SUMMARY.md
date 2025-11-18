# Bash PTY Error - Quick Summary

**For**: Engineering team, agents working with planloop  
**See Full Details**: `docs/bash-pty-errors.md`

---

## The Problem

During long agent sessions, the GitHub Copilot CLI bash tool fails with:
```
<exited with error: posix_spawnp failed.>
```

**When**: After ~30-50 bash commands in a single session  
**Impact**: All bash commands fail, session must be reset  
**Root Cause**: PTY (pseudo-terminal) resource exhaustion/corruption

---

## My Workaround (What I Did)

When bash started failing during the agent-and-prompt-tooling session:

1. **Created fresh bash sessions** with new `sessionId` parameters
2. **Used explicit Python paths**: `.venv/bin/python` instead of `source .venv/bin/activate`
3. **Simplified commands**: Avoided complex chains
4. **Used alternative tools**: `create` instead of `echo >`, `view` instead of `cat`

**Result**: ✅ Successfully completed all 7 tasks despite bash failures

---

## Quick Fix Guide (For Agents)

### When Bash Fails

```python
# Instead of reusing same session
bash(command, sessionId="work")  # Eventually fails

# Use fresh session
bash(command, sessionId=f"task_{task_id}")  # New session per task
```

### Better Alternatives

```python
# Instead of: bash("cat file.txt")
view("/path/to/file.txt")

# Instead of: bash("echo 'content' > file")
create("/path/to/file", "content")

# Instead of: bash("cd /path && .venv/bin/activate && python script")
bash(".venv/bin/python script", sessionId="new_session")
```

---

## Logging & Debugging

### Where Are Logs?

**Copilot CLI Logs**:
- VS Code: View > Output > "GitHub Copilot"
- Command Palette: "Developer: Open Extension Logs Folder"
- JetBrains: Help > Show Log in Finder/Explorer (`idea.log`)

**Planloop Logs**:
```bash
planloop logs --limit 50 --session <session_id>
tail ~/.planloop/sessions/<session_id>/logs/agent-transcript.jsonl
```

### What to Report

When filing issues about bash failures:
1. Command count before failure (~30-50?)
2. Platform (macOS/Linux version)
3. Copilot CLI version
4. Whether workarounds helped

---

## Status & Next Steps

### Current State
- ✅ Issue documented comprehensively (`docs/bash-pty-errors.md`)
- ✅ Workarounds validated in production
- ⏳ Automatic rotation not yet implemented
- ⏳ Not reported to GitHub (waiting for solid repro)

### Planned Improvements
1. **Automatic session rotation** - detect and rotate before failure
2. **Bash wrapper** - `safe_bash()` with retry logic
3. **Agent guidance** - update agents.md with workarounds
4. **Monitoring** - track bash usage per session

---

## Related Issues

- **TTY requirement for `-p` flag**: Different issue, see `docs/lab-testing.md`
- **GitHub Issue #185**: Bash commands not working
- **VS Code #5997**: Agent missing command output

---

**Full Documentation**: See `docs/bash-pty-errors.md` for technical deep dive, logging details, and comprehensive workarounds.
