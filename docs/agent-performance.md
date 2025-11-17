# 📊 Agent Performance Data
**Total Test Runs:** 703

**Latest Run:** `cli-basics-20251117T215342Z-b72c`

## Agent Performance by Model

![claude:unknown](https://img.shields.io/badge/claude_unknown-46.2%25-yellow) **Score:** 41.7/100

![copilot:default](https://img.shields.io/badge/copilot_default-58.3%25-yellow) **Score:** 44.8/100

![openai:unknown](https://img.shields.io/badge/openai_unknown-5.3%25-red) **Score:** 3.5/100

## Detailed Statistics

| Agent+Model | Runs | Passes | Fails | Pass Rate | Avg Score | Top Errors |
|-------------|------|--------|-------|-----------|-----------|------------|
| claude:unknown | 223 | 103 | 120 | 46.2% | 41.7 | missing status-after (105), missing update (102) |
| copilot:default | 381 | 222 | 159 | 58.3% | 44.8 | missing update (130), missing status-after (112) |
| openai:unknown | 263 | 14 | 249 | 5.3% | 3.5 | trace log missing (200), missing status-after (49) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- **Scores:** 0-100 scale based on workflow compliance (status usage, updates, signal handling)
- **Models:** Specific model version used by each agent CLI
- **Real agents tested:** Copilot (gpt-5), Claude (sonnet)
