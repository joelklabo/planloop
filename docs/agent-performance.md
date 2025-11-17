# 📊 Agent Performance Data
**Total Test Runs:** 228

**Latest Run:** `cli-basics-20251117T022117Z-f9ec`

## Agent Performance by Model

![claude:sonnet](https://img.shields.io/badge/claude_sonnet-37.8%25-orange) **Score:** 37.3/100

![copilot:unknown](https://img.shields.io/badge/copilot_unknown-64.3%25-green) **Score:** 51.5/100

![openai:unknown](https://img.shields.io/badge/openai_unknown-33.3%25-orange) **Score:** 17.9/100

## Detailed Statistics

| Agent+Model | Runs | Passes | Fails | Pass Rate | Avg Score | Top Errors |
|-------------|------|--------|-------|-----------|-----------|------------|
| claude:sonnet | 193 | 73 | 120 | 37.8% | 37.3 | missing status-after (105), missing update (102) |
| copilot:unknown | 157 | 101 | 56 | 64.3% | 51.5 | missing update (39), missing status-after (21) |
| openai:unknown | 42 | 14 | 28 | 33.3% | 17.9 | trace log missing (15), missing status-after (13) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- **Scores:** 0-100 scale based on workflow compliance (status usage, updates, signal handling)
- **Models:** Specific model version used by each agent CLI
- **Real agents tested:** Copilot (gpt-5), Claude (sonnet)
