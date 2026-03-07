# EmotionQuant

EmotionQuant is a sentiment-driven quantitative trading system for China A-shares.

## Design Document

`v0.01` historical baseline entry: [`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md)

System doc baseline: `v0.01 Formal Release` (frozen on `2026-03-03`; only errata/link fixes are allowed, no execution-semantics changes).
Freeze record: [`docs/spec/v0.01/records/release-v0.01-formal.md`](docs/spec/v0.01/records/release-v0.01-formal.md)
Current mainline: [`docs/spec/v0.01-plus/README.md`](docs/spec/v0.01-plus/README.md)
Current repository state: `v0.01` is now frozen as a historical attempt; the next implementation restart moves to the `v0.01-plus` mainline. Gate and restart timing should follow the latest status in `docs/spec/common/records/development-status.md`.

Covers: 6-module architecture, MSS/IRS/PAS factor system, L1-L4 data layers, pydantic contracts, 4-week delivery plan.

Backtest scope note: `backtrader` is used only for trading-calendar stepping and data feeding; risk control, matching, position sizing, and state transitions are implemented in the in-house `Broker` kernel.

## Quick Start

### Environment Setup

**Recommended directory structure** (code and data separation):
```
G:\
├── EmotionQuant-gamma\      # Code + Docs (this repo)
├── EmotionQuant_data\       # Local database (not in Git)
└── EmotionQuant-temp\       # Temporary files (not in Git)
```

**Setup steps**:
1. Copy `.env.example` to `.env`
2. Fill in `TUSHARE_TOKEN` (required)
3. Set `DATA_PATH=G:\EmotionQuant_data` (or other path)
4. Set `LOG_PATH=G:\EmotionQuant-temp\logs` (optional)

Detailed setup guide: [`docs/operations/setup-guide.md`](docs/operations/setup-guide.md)

### Install Dependencies

```bash
# Install runtime dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest -v
```

### Basic Usage

```bash
# 1. Fetch data
python main.py fetch --start 2020-01-01 --end 2024-12-31

# 2. Build data layers
python main.py build --layers all

# 3. Run backtest
python main.py backtest --start 2020-01-01 --end 2024-12-31 --patterns bof

# 4. Daily run (Week4 full pipeline)
python main.py run
```

## Directory Structure

```
EmotionQuant-gamma/
├── src/                    # Implementation (6 modules)
│   ├── data/               # Data module (fetcher/cleaner/builder/store)
│   ├── selector/           # Selector module (MSS/IRS/Gene/Selector)
│   ├── strategy/           # Strategy module (PAS/Registry/Strategy)
│   ├── broker/             # Broker module (Risk/Matcher)
│   ├── backtest/           # Backtest module (Engine)
│   └── report/             # Report module (Reporter)
├── tests/                  # Automated tests
│   ├── unit/               # Unit tests (organized by module)
│   ├── integration/        # Integration tests (cross-module call chains)
│   └── patches/            # Patch/regression tests (prevent historical bugs)
├── scripts/                # Utility scripts
│   ├── data/               # Data-related tools
│   ├── backtest/           # Backtest-related tools
│   ├── report/             # Report-related tools
│   ├── ops/                # Operations tools
│   └── setup/              # Environment setup tools
├── docs/                   # Documentation entry (see docs/README.md)
│   ├── design-v2/          # System design (Single Source of Truth)
│   │   ├── 01-system/      # System-level design (`v0.01 Frozen` historical baseline)
│   │   ├── 02-modules/     # Module-level design
│   │   └── 03-algorithms/  # Algorithm-level design (MSS/IRS/PAS)
│   ├── Strategy/           # Strategy theoretical foundations (MSS/IRS/PAS)
│   ├── observatory/        # Macro observation and verification
│   ├── spec/               # Stage-specific archives (v0.01-v0.06)
│   │   ├── v0.01/          # v0.01 stage materials
│   │   ├── v0.02/          # v0.02 stage materials
│   │   ├── ...             # v0.03-v0.06
│   │   └── common/         # Cross-version documents
│   ├── steering/           # Governance rules (12 product principles)
│   ├── reference/          # Reference materials
│   │   ├── a-stock-rules/  # A-share market rules
│   │   └── operations/     # Operations guides
│   └── workflow/           # Workflow processes
├── .env.example            # Environment variable template
├── pyproject.toml          # Project configuration and dependencies
├── main.py                 # CLI entry point
└── README.md               # This file
```

**Documentation Architecture**:
- **Three Pillars**: `design-v2/` (system design), `Strategy/` (strategy theory), `observatory/` (observation & verification)
- **Three Supports**: `steering/` (governance rules), `spec/` (stage archives), `workflow/` (processes)
- **Two Auxiliaries**: `reference/` (reference materials), `README.md` (navigation)

See: [`docs/README.md`](docs/README.md). The historical reorganization report remains in [`docs/REORGANIZATION-COMPLETE-REPORT.md`](docs/REORGANIZATION-COMPLETE-REPORT.md) for traceability only.

## Related Documentation

- 📖 **Setup Guide**: [`docs/operations/setup-guide.md`](docs/operations/setup-guide.md) - Detailed environment setup
- 📖 **v0.01 Historical Baseline**: [`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md) - Frozen system baseline
- 📖 **Current Mainline**: [`docs/spec/v0.01-plus/README.md`](docs/spec/v0.01-plus/README.md) - `v0.01-plus` replacement line entry
- 📖 **Documentation**: [`docs/README.md`](docs/README.md) - Complete documentation index
- 📖 **Current Status**: [`docs/spec/common/records/development-status.md`](docs/spec/common/records/development-status.md) - Current governance state and restart gate
- 📖 **Development Rules**: [`AGENTS.md`](AGENTS.md) - Agent development rules

## License

MIT (see [`LICENSE`](LICENSE))



