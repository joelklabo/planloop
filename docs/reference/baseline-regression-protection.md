# Baseline Regression Protection

## Overview

The regression protection system prevents unintentional performance degradation when optimizing agent prompts. It tracks baseline performance for each agent and alerts when changes cause significant regressions.

## Components

### 1. Baseline Configuration (`labs/baseline.json`)

Version-controlled JSON file tracking baseline performance for each agent:

```json
{
  "copilot": {
    "pass_rate": 58.3,
    "avg_score": 44.8,
    "version": "v0.3.1",
    "last_updated": "2025-11-17",
    "prompt_file": "labs/prompts/copilot-v0.3.1.txt",
    "notes": "Baseline established after environment setup improvements"
  },
  "config": {
    "regression_threshold": 5.0,
    "description": "Maximum acceptable drop in pass rate before alerting"
  }
}
```

### 2. Baseline Checker (`labs/check_baseline.sh`)

Compares current Copilot performance against baseline:

```bash
./labs/check_baseline.sh
```

**Exit codes**:
- `0`: No regression detected
- `1`: Significant regression detected (>5% drop in pass rate)

**Output**:
```
=== Checking Copilot Baseline ===
Baseline: 58.3% pass rate, 44.8 avg score
Current:  60.2% pass rate, 46.0 avg score

✅ No significant regression detected ↑
```

### 3. Baseline Updater (`labs/update_baseline.sh`)

Updates baseline values when improvements are made:

```bash
# Auto-detect current performance
./labs/update_baseline.sh copilot --auto-detect

# Manual entry
./labs/update_baseline.sh copilot
```

**Workflow**:
1. Detects current performance from `labs/metrics.json`
2. Prompts for confirmation
3. Requests prompt version and notes
4. Updates `labs/baseline.json`
5. Reminds to commit the changes

### 4. CI Integration

GitHub Actions workflow automatically checks for regressions when:
- Commit messages contain "prompt" or "Optimize"
- Files in `labs/prompts/` or `labs/agents/` are modified
- `labs/baseline.json` is modified

**CI Job**: `baseline-regression-check`

If regression detected:
```
⚠️  Baseline regression detected!
If this is intentional, update the baseline:
  ./labs/update_baseline.sh copilot --auto-detect

Include the updated labs/baseline.json in your commit.
```

## Workflow

### Optimizing Agent Prompts

1. **Before optimization**: Check current baseline
   ```bash
   ./labs/check_baseline.sh
   ```

2. **Make prompt changes**: Edit prompt files in `labs/prompts/` or `labs/agents/`

3. **Test changes**: Run iterations
   ```bash
   ./labs/run_iterations.sh 30 cli-basics claude
   ```

4. **Check for regression**: After optimization
   ```bash
   ./labs/check_baseline.sh
   ```

5. **If Copilot improved**: Update baseline
   ```bash
   ./labs/update_baseline.sh copilot --auto-detect
   git add labs/baseline.json
   ```

6. **Commit**: Include baseline updates with prompt changes
   ```bash
   git commit -m "Optimize Claude prompt to 55%
   
   - Updated Claude prompt structure
   - Pass rate improved from 46% to 55%
   - Updated Copilot baseline to 60.2% (no regression)"
   ```

### Using optimize_safely.sh

The safe optimization script automates this workflow:

```bash
./labs/optimize_safely.sh claude 30
```

**Steps**:
1. Checks Copilot baseline
2. Snapshots current metrics
3. Runs optimization iterations
4. Checks for regression
5. Reports results or alerts on regression

## Configuration

### Regression Threshold

Default: 5.0% (pass rate drop)

To change, edit `labs/baseline.json`:
```json
{
  "config": {
    "regression_threshold": 3.0
  }
}
```

### Tracked Agents

Currently tracking:
- **Copilot** (primary - regression protection enforced)
- **Claude** (secondary - for reference)
- **OpenAI** (tertiary - for reference)

## Design Rationale

### Why Copilot-Focused?

Copilot has the highest baseline performance (58.3%) and is the primary target. When optimizing Claude or OpenAI, we must ensure Copilot doesn't regress.

### Why Version-Controlled Baseline?

1. **Transparency**: All baseline changes are tracked in git history
2. **Reproducibility**: Any commit can be checked against its baseline
3. **Accountability**: Baseline updates require explicit commits
4. **Documentation**: Git log shows why baselines changed

### Why 5% Threshold?

- Small enough to catch meaningful regressions
- Large enough to avoid false positives from variance
- Based on statistical analysis of 700+ test runs

## Troubleshooting

### False Positive: "Regression detected" but performance is stable

**Cause**: Baseline may be outdated  
**Solution**: Update baseline if current performance is consistently higher
```bash
./labs/update_baseline.sh copilot --auto-detect
```

### CI failing on baseline check

**Cause**: Prompt changes affected Copilot negatively  
**Solutions**:
1. **Revert prompt changes** if unintentional
2. **Use agent-specific prompts** if necessary
3. **Update baseline** if regression is acceptable trade-off

### Baseline updater can't find metrics

**Cause**: `labs/metrics.json` doesn't have recent data  
**Solution**: Run lab tests first
```bash
./labs/run_iterations.sh 10 cli-basics copilot
python3 labs/aggregate_metrics.py
```

## Testing

Test suite: `tests/test_regression_protection.py`

**Coverage**:
- ✅ Baseline config file exists
- ✅ Config has proper structure
- ✅ Values are reasonable (0-100 ranges)
- ✅ check_baseline.sh reads from JSON
- ✅ CI workflow includes regression check
- ✅ Update script exists and is executable

Run tests:
```bash
pytest tests/test_regression_protection.py -v
```

## Future Enhancements

1. **Multi-Agent Protection**: Extend to Claude and OpenAI once they reach 60%+
2. **Automated Rollback**: Auto-revert commits that cause regressions
3. **Performance Tracking**: Long-term trend analysis
4. **Baseline Recommendations**: Suggest when to update baselines
5. **A/B Testing Integration**: Compare prompt variations safely

## See Also

- `docs/reference/successful-prompt-patterns.md` - Documented prompt patterns
- `docs/lab-testing.md` - Lab testing infrastructure
- `docs/agent-performance.md` - Current agent metrics
- `labs/optimize_safely.sh` - Safe optimization workflow
