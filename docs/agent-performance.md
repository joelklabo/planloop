# 📊 Agent Performance Data

**Total Test Runs:** 43

**Latest Run:** `cli-basics-20251116T204252Z-e038`


## Agent Compliance Rates

![claude](https://img.shields.io/badge/claude-22.0%25-red)
![copilot](https://img.shields.io/badge/copilot-21.4%25-red)
![openai](https://img.shields.io/badge/openai-33.3%25-red)

## Detailed Statistics

| Agent | Runs | Passes | Fails | Pass Rate | Top Errors |
|-------|------|--------|-------|-----------|------------|
| claude | 41 | 9 | 32 | 22.0% | missing status-after (18), trace log missing (14) |
| copilot | 42 | 9 | 33 | 21.4% | missing status-after (17), trace log missing (16) |
| openai | 42 | 14 | 28 | 33.3% | trace log missing (15), missing status-after (13) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- Metrics track: status command usage, update command usage, proper workflow sequence
- Updated automatically via GitHub Actions (see `.github/workflows/update-metrics.yml`)
