# 📊 Agent Performance Data
**Total Test Runs:** 334

**Latest Run:** `cli-basics-20251117T054602Z-6731`

## Agent Performance by Model

![claude:unknown](https://img.shields.io/badge/claude_unknown-37.8%25-orange) **Score:** 37.3/100

![copilot:gpt-5](https://img.shields.io/badge/copilot_gpt--5-46.2%25-yellow) **Score:** 38.5/100

![openai:unknown](https://img.shields.io/badge/openai_unknown-17.5%25-red) **Score:** 11.6/100

## Detailed Statistics

| Agent+Model | Runs | Passes | Fails | Pass Rate | Avg Score | Top Errors |
|-------------|------|--------|-------|-----------|-----------|------------|
| claude:unknown | 193 | 73 | 120 | 37.8% | 37.3 | missing status-after (105), missing update (102) |
| copilot:gpt-5 | 225 | 104 | 121 | 46.2% | 38.5 | missing update (104), missing status-after (86) |
| openai:unknown | 80 | 14 | 66 | 17.5% | 11.6 | missing status-after (49), missing update (45) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- **Scores:** 0-100 scale based on workflow compliance (status usage, updates, signal handling)
- **Models:** Specific model version used by each agent CLI
- **Real agents tested:** Copilot (gpt-5), Claude (sonnet)
