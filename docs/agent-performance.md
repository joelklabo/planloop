# 📊 Agent Performance Data
**Total Test Runs:** 266

**Latest Run:** `cli-basics-20251117T031130Z-c721`

## Agent Performance by Model

![claude:unknown](https://img.shields.io/badge/claude_unknown-37.8%25-orange) **Score:** 37.3/100

![copilot:unknown](https://img.shields.io/badge/copilot_unknown-64.3%25-green) **Score:** 51.5/100

![openai:gpt-4](https://img.shields.io/badge/openai_gpt--4-17.5%25-red) **Score:** 11.6/100

## Detailed Statistics

| Agent+Model | Runs | Passes | Fails | Pass Rate | Avg Score | Top Errors |
|-------------|------|--------|-------|-----------|-----------|------------|
| claude:unknown | 193 | 73 | 120 | 37.8% | 37.3 | missing status-after (105), missing update (102) |
| copilot:unknown | 157 | 101 | 56 | 64.3% | 51.5 | missing update (39), missing status-after (21) |
| openai:gpt-4 | 80 | 14 | 66 | 17.5% | 11.6 | missing status-after (49), missing update (45) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- **Scores:** 0-100 scale based on workflow compliance (status usage, updates, signal handling)
- **Models:** Specific model version used by each agent CLI
- **Real agents tested:** Copilot (gpt-5), Claude (sonnet)
