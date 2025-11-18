# Agent Testing Reference

Quick reference for testing AI agents with planloop's lab infrastructure.

**Last Updated**: 2025-11-17

---

## Output Capture Methods

| Agent | Capture | Method | Notes |
|-------|---------|--------|-------|
| **Copilot** | ✅ Yes | `gh copilot suggest -t shell "prompt" 2>&1` | May require auth refresh |
| **Claude** | ✅ Yes | `claude "prompt" 2>&1` | Best for automation |
| **Codex** | ⚠️ Limited | N/A | Requires TTY; difficult to automate |

### Transcript Access
- Programmatic capture stores output in `labs/results/<run_id>/<agent>/`
  - `stdout.txt` - Standard output
  - `stderr.txt` - Standard error
  - `transcript.txt` - Combined conversation
- Includes agent thinking, tool calls, and responses

---

## Common Issues & Solutions

### GitHub Copilot

**Authentication Failure**
- **Symptom**: Exit code 1, no output, silent failure after 6-8 seconds
- **Cause**: Invalid GitHub token in keyring
- **Solution**:
  ```bash
  gh auth status  # Check status
  gh auth login --web -h github.com  # Re-authenticate via OAuth
  ```

**Token Authentication** (Limited)
- Accepts fine-grained PATs via `GH_TOKEN` environment variable
- Must start with `github_pat_` and have "Copilot Requests" permission
- OAuth via `gh auth login` is more reliable
- Classic PATs may work but not recommended

**Rate Limits**
- Check stderr/stdout for "rate limit", "usage limit", "quota exceeded"
- Wait for reset (usually hourly or daily)

**Debug Logging**
```bash
gh copilot suggest -t shell "prompt" \
  --log-level debug \
  --log-dir ./tmp/logs
```

### Claude

**API Key Issues**
- Set via environment: `export ANTHROPIC_API_KEY=sk-...`
- Or config file (check Claude CLI docs)

### Codex/OpenAI

**API Key Issues**
- Set via environment: `export OPENAI_API_KEY=sk-...`
- Check API usage limits on OpenAI dashboard

---

## Debug Flags & Logging

### Copilot CLI
- `--log-level`: `none`, `error`, `warning`, `info`, `debug`, `all`, `default`
- `--log-dir <path>`: Specify log directory
- Session logs: `session-<uuid>.log`

### Claude CLI
- Check CLI docs for verbose/debug modes (varies by version)

### General Tips
- Capture both stdout and stderr: `command 2>&1`
- Use `tee` to log and display: `command 2>&1 | tee output.log`
- Set environment variables for API keys before running
- Test authentication separately before automation

---

## Quick Testing Checklist

Before running automated tests:
1. ✅ Check authentication: `gh auth status`, API keys set
2. ✅ Test command manually first
3. ✅ Verify output capture works
4. ✅ Check rate limits haven't been hit
5. ✅ Enable debug logging if issues occur
