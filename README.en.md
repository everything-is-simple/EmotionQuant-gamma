# EmotionQuant

EmotionQuant is a sentiment-driven quantitative trading system for China A-shares.

## Design Document

Single authoritative entry: [`docs/design-v2/rebuild-v0.01.md`](docs/design-v2/rebuild-v0.01.md)

System doc baseline: `v0.01 Formal Release` (frozen on `2026-03-03`; only errata/link fixes are allowed, no execution-semantics changes).
Freeze record: [`docs/design-v2/release-v0.01-formal.md`](docs/design-v2/release-v0.01-formal.md)

Covers: 6-module architecture, MSS/IRS/PAS factor system, L1-L4 data layers, pydantic contracts, 4-week delivery plan.

Backtest scope note: `backtrader` is used only for trading-calendar stepping and data feeding; risk control, matching, position sizing, and state transitions are implemented in the in-house `Broker` kernel.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Development dependencies
pip install -e ".[dev]"

# Run tests
pytest -v
```

## Directory Structure

- `src/` — Implementation (Data / Selector / Strategy / Broker / Backtest / Report)
- `tests/` — Automated tests
- `docs/design-v2/` — Current design documents
- `docs/archive/` — Historical archives (read-only)

## Configuration

Copy `.env.example` to `.env` and fill in actual values. Key variables:

- `TUSHARE_TOKEN` — TuShare API token
- `DATA_PATH` — Data root directory (outside repo)

## License

MIT (see [`LICENSE`](LICENSE))
