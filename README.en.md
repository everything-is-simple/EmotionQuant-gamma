# EmotionQuant

EmotionQuant is a sentiment-driven quantitative system for China A-shares.

## Design Entry

- `v0.01` historical baseline: [`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md)
- `v0.01-plus` current mainline: [`docs/spec/v0.01-plus/README.md`](docs/spec/v0.01-plus/README.md)
- Current mainline design SoT: [`docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`](docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md)
- Current governance status: [`docs/spec/common/records/development-status.md`](docs/spec/common/records/development-status.md)

Current mainline execution pipeline:

`Selector preselection -> BOF trigger -> IRS ranking -> MSS position control -> Broker execution`

Notes:
- `v0.01` is frozen as a historical attempt for comparison, rollback, and regression only.
- `v0.01-plus` is the current mainline.
- `backtrader` is used only for calendar stepping and data feeding; risk, matching, sizing, and state transitions are handled by the in-house `Broker` kernel.

## Quick Start

### Environment Setup

**Recommended directory structure**:
```text
G:\
├── EmotionQuant-gamma\      # code + docs (this repo)
├── EmotionQuant_data\       # local database (not in Git)
└── EmotionQuant-temp\       # temporary files (not in Git)
```

**Setup steps**:
1. Copy `.env.example` to `.env`
2. Fill in `TUSHARE_TOKEN`
3. Set `DATA_PATH=G:\EmotionQuant_data`
4. Set `LOG_PATH=G:\EmotionQuant-temp\logs` when needed

Detailed setup guide: [`docs/operations/setup-guide.md`](docs/operations/setup-guide.md)

### Install Dependencies

```bash
pip install -e .
pip install -e ".[dev]"
pytest -v
```

### Basic Usage

```bash
python main.py fetch --start 2020-01-01 --end 2024-12-31
python main.py build --layers all
python main.py backtest --start 2020-01-01 --end 2024-12-31 --patterns bof
python main.py run
```

## Repository Layout

```text
EmotionQuant-gamma/
├── src/                    # implementation code (6 modules)
├── tests/                  # automated tests (unit/integration/patches)
├── scripts/                # utilities (data/backtest/report/ops/setup)
├── docs/                   # documentation entry (see docs/README.md)
│   ├── design-v2/          # system design; includes v0.01 Frozen baseline and current algorithm design
│   ├── Strategy/           # theory sources and methodology tracing
│   ├── observatory/        # observation, review, and retrospectives
│   ├── spec/               # versioned archives and current mainline material
│   ├── steering/           # governance constraints
│   ├── reference/          # external references
│   └── workflow/           # fixed execution flow
├── .env.example
├── pyproject.toml
├── main.py
└── README.md
```

## Related Docs

- Setup guide: [`docs/operations/setup-guide.md`](docs/operations/setup-guide.md)
- Documentation index: [`docs/README.md`](docs/README.md)
- Current status: [`docs/spec/common/records/development-status.md`](docs/spec/common/records/development-status.md)
- Mainline roadmap: [`docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`](docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md)
- Agent rules: [`AGENTS.md`](AGENTS.md)

## License

MIT (see [`LICENSE`](LICENSE))
