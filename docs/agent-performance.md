# 📊 Agent Performance Data
**Total Test Runs:** 50

**Latest Run:** `cli-basics-20251116T210925Z-3c54`

## Agent Performance by Model

![claude:sonnet](https://img.shields.io/badge/claude_sonnet-26.1%25-orange) **Score:** 21.8/100

![copilot:gpt-5](https://img.shields.io/badge/copilot_gpt--5-26.5%25-orange) **Score:** 21.7/100

![openai:unknown](https://img.shields.io/badge/openai_unknown-33.3%25-orange) **Score:** 17.9/100

## Detailed Statistics

| Agent+Model | Runs | Passes | Fails | Pass Rate | Avg Score | Top Errors |
|-------------|------|--------|-------|-----------|-----------|------------|
| claude:sonnet | 46 | 12 | 34 | 26.1% | 21.8 | missing status-after (20), missing update (16) |
| copilot:gpt-5 | 49 | 13 | 36 | 26.5% | 21.7 | missing update (19), missing status-after (18) |
| openai:unknown | 42 | 14 | 28 | 33.3% | 17.9 | trace log missing (15), missing status-after (13) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- **Scores:** 0-100 scale based on workflow compliance (status usage, updates, signal handling)
- **Models:** Specific model version used by each agent CLI
- **Real agents tested:** Copilot (gpt-5), Claude (sonnet)
