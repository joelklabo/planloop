# 📊 Agent Performance Data
**Total Test Runs:** 251

**Latest Run:** `cli-basics-20251117T030632Z-e41d`

## Agent Performance by Model

![claude:unknown](https://img.shields.io/badge/claude_unknown-37.8%25-orange) **Score:** 37.3/100

![copilot:unknown](https://img.shields.io/badge/copilot_unknown-64.3%25-green) **Score:** 51.5/100

![openai:gpt-4](https://img.shields.io/badge/openai_gpt--4-21.5%25-orange) **Score:** 13.2/100

## Detailed Statistics

| Agent+Model | Runs | Passes | Fails | Pass Rate | Avg Score | Top Errors |
|-------------|------|--------|-------|-----------|-----------|------------|
| claude:unknown | 193 | 73 | 120 | 37.8% | 37.3 | missing status-after (105), missing update (102) |
| copilot:unknown | 157 | 101 | 56 | 64.3% | 51.5 | missing update (39), missing status-after (21) |
| openai:gpt-4 | 65 | 14 | 51 | 21.5% | 13.2 | missing status-after (34), missing update (30) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- **Scores:** 0-100 scale based on workflow compliance (status usage, updates, signal handling)
- **Models:** Specific model version used by each agent CLI
- **Real agents tested:** Copilot (gpt-5), Claude (sonnet)
