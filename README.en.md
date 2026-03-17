# EmotionQuant

EmotionQuant is a China A-share trading system organized around four battlefields:

1. `blueprint/`: mainline governance and default runtime authority.
2. `normandy/`: alpha truth and entry/exit diagnosis research.
3. `positioning/`: sizing, exit control, and execution discipline research.
4. `gene/`: historical trend/wave context research.

## Current Runtime

The current governed default runtime is:

`Selector preselection -> BOF baseline entry -> FIXED_NOTIONAL_CONTROL -> FULL_EXIT_CONTROL -> Broker execution`

Important boundaries:

1. `Gene` is active as context sidecar / attribution layer, not as runtime hard gate.
2. Legacy `IRS/MSS` are no longer the default execution spine.
3. `scripts/backtest/` contains evidence runners, not the default system entry.

## Current Data Foundation

The data layer is now `TDX local-first`.

Primary foundation:

1. Local Tongdaxin `vipdoc` provides historical stock/index daily data.
2. Local `T0002/hq_cache` provides stock list and industry member snapshots.
3. Local rules provide `up_limit/down_limit`.

Fallback sources:

1. `BaoStock` for small-window gap filling.
2. `TuShare` as legacy emergency fallback.

See:

- [`scripts/data/README.md`](scripts/data/README.md)
- [`docs/reference/code-maps/src-data-code-map-20260318.md`](docs/reference/code-maps/src-data-code-map-20260318.md)
- Historical baseline: [`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md)

## Design Entry

- Current four-battlefield system map: [`docs/spec/common/records/four-battlefields-integrated-system-map-20260316.md`](docs/spec/common/records/four-battlefields-integrated-system-map-20260316.md)
- Mainline authority: [`blueprint/README.md`](blueprint/README.md)
- Governance status ledger: [`docs/spec/common/records/development-status.md`](docs/spec/common/records/development-status.md)
- Documentation shelf: [`docs/navigation/four-battlefields-document-shelf/README.md`](docs/navigation/four-battlefields-document-shelf/README.md)
- Historical baseline authority: [`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md)

## Daily Maintenance

The recommended daily local update flow is:

1. Download latest Tongdaxin local files after market close.
2. Run `scripts/data/import_tdx_vipdoc.py`.
3. Run `scripts/data/import_tdx_static_assets.py`.
4. Run `scripts/data/repair_l1_partitions_from_raw_duckdb.py`.

Detailed usage is documented in [`scripts/data/README.md`](scripts/data/README.md).

## Quick Start

### Environment

Recommended directory layout:

```text
G:\
├─ EmotionQuant-gamma\   # code + docs
├─ EmotionQuant_data\    # local databases and artifacts
└─ EmotionQuant-temp\    # temp/runtime files
```

Setup:

1. Copy `.env.example` to `.env`.
2. Fill in `DATA_PATH`, `TEMP_PATH`, and optional `RAW_DB_PATH`.
3. Install dependencies.

### Install

```bash
pip install -e .
pip install -e ".[dev]"
```

### Common Commands

```bash
python main.py fetch --from-raw-db G:\EmotionQuant_data\duckdb\emotionquant.duckdb --start 2026-03-01 --end 2026-03-18
python main.py build --layers l2,l3 --start 2026-03-01 --end 2026-03-18
python main.py backtest --start 2024-01-01 --end 2024-12-31 --patterns bof
```

## Related Docs

- [`docs/README.md`](docs/README.md)
- [`docs/reference/operations/current-mainline-operating-runbook-20260317.md`](docs/reference/operations/current-mainline-operating-runbook-20260317.md)
- [`scripts/data/README.md`](scripts/data/README.md)
- [`scripts/backtest/README.md`](scripts/backtest/README.md)
- [`scripts/ops/README.md`](scripts/ops/README.md)

## License

MIT. See [`LICENSE`](LICENSE).
