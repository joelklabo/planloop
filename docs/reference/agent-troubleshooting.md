# Agent Troubleshooting Guide

This document covers common issues when working with different AI agents and how to resolve them.

## GitHub Copilot CLI

### Authentication Issues

**Symptom:** Copilot exits with code 1, no output, fails silently after ~6-8 seconds

**Root Cause:** Invalid GitHub authentication token in keyring

**Solution:**
```bash
gh auth status  # Check current auth status
gh auth login -h github.com  # Re-authenticate
```

**Verification:**
- Interactive mode should work: `copilot --allow-all-tools --allow-all-paths`
- Prompt mode should work: `copilot -p "echo hello" --allow-all-tools --allow-all-paths --model gpt-5`

### Rate Limits

**Symptom:** Error messages containing "rate limit", "usage limit", or "quota exceeded"

**Detection:** Check stderr/stdout for rate limit keywords

**Solution:** Wait for rate limit to reset (usually hourly or daily)

### Model Specification

**Current Working Model:** `gpt-5`

**Command Format:**
```bash
copilot -p "<prompt>" --allow-all-tools --allow-all-paths --model gpt-5
```

**CRITICAL Notes (v0.0.358):**
- `--allow-all-tools` is REQUIRED for non-interactive mode
- `--allow-all-paths` prevents file access restrictions
- **DO NOT USE `--no-color`** - causes silent exit code 1 failure in v0.0.358
- **DO NOT redirect stdout/stderr directly** - Copilot requires TTY-like behavior, use `tee` instead:
  ```bash
  copilot -p "$prompt" ... 2>&1 | tee output.txt
  ```

### Debug Logging

**Enable Debug Logs:**
```bash
copilot -p "<prompt>" \
  --allow-all-tools \
  --allow-all-paths \
  --model gpt-5 \
  --log-level debug \
  --log-dir ./tmp/copilot_logs
```

**Log Levels:** `none`, `error`, `warning`, `info`, `debug`, `all`, `default`

**Default Log Location:** `~/.copilot/logs/`

**What to Check in Logs:**
- Authentication failures
- API request/response details
- Rate limit errors
- Model selection issues
- Tool execution traces

---

## Claude (Anthropic)

### Rate Limits

**Symptom:** API errors about usage limits

**Detection:** Check for rate limit keywords in error output

**Solution:** Wait for rate limit reset or upgrade API tier

### Prompt Format

**Best Practice:** Use XML tags for structure
```
<instructions>
...
</instructions>

<examples>
...
</examples>
```

**Avoid:** Complex markdown formatting in prompts

---

## OpenAI (Codex)

### Authentication

**Required:** OpenAI API key in environment or config

**Setup:**
```bash
export OPENAI_API_KEY="sk-..."
```

### Rate Limits

**Symptom:** 429 errors or insufficient quota messages

**Solution:** 
- Add credits to OpenAI account
- Check billing and usage limits
- Wait for rate limit reset

### Model Specification

**Current Model:** Should match Copilot's underlying model when possible

---

## General Debugging Steps

### 1. Check Agent Availability
```bash
# Copilot
which copilot && copilot --version

# Claude  
which claude && claude --version

# OpenAI/Codex
# Check API key is set
echo $OPENAI_API_KEY | cut -c1-10
```

### 2. Test Basic Functionality
```bash
# Copilot interactive
copilot --allow-all-tools --allow-all-paths

# Copilot prompt mode (v0.0.358+)
copilot -p "echo hello" --allow-all-tools --allow-all-paths --model gpt-5
```

### 3. Check Authentication
```bash
# GitHub (for Copilot)
gh auth status

# OpenAI
# Verify API key works with curl
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.data[0]'
```

### 4. Review Trace Logs

For lab runs, check:
- `labs/results/<run-id>/<agent>/trace.log` - Timing and events
- `labs/results/<run-id>/<agent>/stdout.txt` - Agent output
- `labs/results/<run-id>/<agent>/stderr.txt` - Error messages

**Common Patterns:**
- Exit code 1 + empty output = Authentication failure
- Exit code 2 = Rate limit (by convention in our adapters)
- Long runtime + exit code 1 = Prompt issue or internal error

### 5. Test Prompt Length

If agent fails with complex prompts:
1. Test with minimal prompt: `"echo hello"`
2. Gradually increase complexity
3. Check for special characters that need escaping
4. Verify prompt doesn't exceed model's context window

---

## Prompt Engineering Issues

### Silent Failures

**Problem:** Agent runs but doesn't follow instructions

**Common Causes:**
- Prompt too long or complex
- Instructions buried in middle of prompt
- Conflicting instructions
- Agent doesn't understand domain-specific commands

**Solutions:**
- Put critical instructions at START and END of prompt
- Use CAPS for emphasis (not markdown)
- Repeat critical steps multiple times
- Show exact command examples
- Test with simple scenarios first

### Compliance Failures

See `docs/reference/agent-prompting-guide.md` for specific prompt optimization strategies per agent.

---

## Lab Testing Specific Issues

### All Runs Failing

**Check:**
1. Authentication (especially after system updates)
2. Rate limits (especially after many test runs)
3. Recent agent CLI updates (check versions)
4. Prompt changes (revert to known working version)

**Quick Test:**
```bash
# Run single iteration with verbose output
./labs/run_iterations.sh 1 cli-basics copilot

# Check latest results
cat labs/results/*/copilot/trace.log
cat labs/results/*/copilot/stderr.txt
```

### Baseline Regression

If previously working prompts start failing:
1. Check git history for prompt changes
2. Revert to last known working version
3. Test with small sample (3-5 runs)
4. Compare trace logs from working vs failing runs

---

## Prevention

### Before Major Test Runs

1. Test authentication: `gh auth status`
2. Check rate limits haven't been hit recently
3. Verify with small test run (1-3 iterations)
4. Save working prompt versions in git

### After Agent Updates

When Copilot/Claude/OpenAI CLIs update:
1. Test basic functionality first
2. Check for breaking changes in release notes
3. Update adapter scripts if needed
4. Re-baseline with small test run

### Monitoring

Add to pre-test checklist:
- [ ] `gh auth status` shows valid token
- [ ] Test prompt mode: `copilot -p "echo test" --allow-all-tools --allow-all-paths --no-color`
- [ ] No recent rate limit errors in logs
- [ ] Sufficient API credits (for paid services)
