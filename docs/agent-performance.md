# 📊 Agent Performance Data

**Total Test Runs:** 35

**Latest Run:** `cli-basics-20251116T085040Z-6fc8`


## Agent Compliance Rates

![claude](https://img.shields.io/badge/claude-6.1%25-red)
![copilot](https://img.shields.io/badge/copilot-5.9%25-red)
![openai](https://img.shields.io/badge/openai-20.6%25-red)

## Detailed Statistics

| Agent | Runs | Passes | Fails | Pass Rate | Top Errors |
|-------|------|--------|-------|-----------|------------|
| claude | 33 | 2 | 31 | 6.1% | missing status-after (18), missing update (14) |
| copilot | 34 | 2 | 32 | 5.9% | missing status-after (17), missing update (16) |
| openai | 34 | 7 | 27 | 20.6% | trace log missing (14), missing status-after (13) |

## Notes

- Data collected from automated lab runs testing agent compliance with planloop workflow
- Metrics track: status command usage, update command usage, proper workflow sequence
- Updated automatically via GitHub Actions (see `.github/workflows/update-metrics.yml`)
