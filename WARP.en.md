# WARP.en.md

This file provides minimal, executable repository rules for automated agents. Content is equivalent to `AGENTS.md`, `AGENTS.en.md`, `CLAUDE.md`, `CLAUDE.en.md`, `WARP.md`, and `WARP.en.md`, targeting generic agent runtimes.

**Document Version**: `v0.01-plus Mainline Replacement`  
**Document Status**: `Active`  
**Freeze Date**: `Not Applicable (Active SoT)`  
**Change Policy**: `Controlled updates are allowed as long as the v0.01 Frozen historical baseline is preserved.`

---

## 1. Document Positioning

- Purpose: minimal, executable repository rules for automated agents.
- **v0.01 historical baseline entry**: `docs/design-v2/01-system/system-baseline.md` (frozen system baseline)
- **Current mainline entry**: `docs/spec/v0.01-plus/README.md`
- **Current design SoT**: `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
- Stage documents are archived under `docs/spec/`; reference materials are under `docs/reference/`
- **Current governance status**: `docs/spec/common/records/development-status.md`

---

## 2. System Positioning

EmotionQuant is a sentiment-driven quantitative system for China A-shares.

- Solo developer project
- Execution model: **4-week incremental delivery**
- Documentation serves implementation

---

## 3. Current Mainline Iron Laws (v0.01-plus)

1. **Current mainline pipeline = Selector preselection -> BOF trigger -> IRS ranking -> MSS position control -> Broker execution.**
2. **v0.01 Frozen remains only as historical comparison and rollback reference.**
3. **Selector only performs basic filtering and scale control; it must not perform MSS gate / IRS filter trade decisions.**
4. **IRS is industry-level cross-sectional enhancement only; no hard pre-filtering.**
5. **MSS is market-level risk control only; it must not enter the stock-level cross-sectional total score.**
6. **PAS is a framework concept; the current mainline still implements BOF only.**
7. **Modules pass result contracts only, never internal intermediate features.**
8. **Backtest and paper trading share the same broker kernel.**
9. **No hardcoded paths or secrets**; everything is injected via `config.py`.
10. **Execution semantics are fixed to T+1 Open**: `signal_date=T`, `execute_date=T+1`, fill price = `T+1` open.

Details: `docs/spec/v0.01-plus/README.md` and `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`

---

## 4. Development Flow

- Execution model: 4-week incremental delivery
- Each week must produce independently verifiable deliverables (runnable code + passing tests)
- Branch naming: `rebuild/{module}`, merge target `main`

---

## 5. Data Contracts

Inter-module data is passed as pydantic objects (`contracts.py`):
- `MarketScore` (MSS output; consumed by `Broker / Risk` on the current mainline)
- `IndustryScore` (IRS output; consumed by `Strategy / Ranker` on the current mainline)
- `StockCandidate` (Selector -> Strategy)
- `Signal` (Strategy -> Broker)
- `Order` / `Trade` (Broker internal -> Report)

Code uses English; comments/docs/UI use Chinese. Uniform `snake_case`.
L1 uses `ts_code` (TuShare format); L2+ uses `code` (6-digit pure code).

Details: `docs/spec/v0.01-plus/governance/v0.01-plus-data-contract-table.md`

---

## 6. Data And Directory Discipline

DuckDB uses a single database with L1-L4 decoupling. The data root is injected by the `DATA_PATH` environment variable outside the repository.

| Layer | Content |
|------|------|
| L1 | Raw data |
| L2 | Processed data |
| L3 | Algorithm output |
| L4 | Historical analysis cache |

**Dependency rule**: L2 reads only L1; L3 reads only L1/L2; L4 reads only L1/L2/L3. Reverse dependencies are forbidden.

**Directory discipline (mandatory)**:
- `G:\EmotionQuant-gamma` stores code, docs, configs, and required scripts only.
- `G:\EmotionQuant_data` stores local databases, logs, and long-lived data artifacts.
- `G:\EmotionQuant-temp` stores temp files, runtime copies, experiment caches, and intermediate artifacts.

---

## 7. Architecture (6 Modules)

| Module | Responsibility |
|--------|---------------|
| Data | Fetch, clean, store, cache algorithm output |
| Selector | Basic filtering + scale control + `preselect_score` |
| Strategy | `BOF` trigger + `IRS` ranking |
| Broker | `MSS` risk overlay + matching |
| Backtest | Historical backtesting |
| Report | Reports + alerts + attribution |

---

## 8. Governance Structure

### 8.1 Directory Positioning

| Directory | Role |
|-----------|------|
| `docs/design-v2/` | System-level design docs (`system-baseline.md` is the `v0.01 Frozen` historical baseline; `v0.01-plus` design entry is `down-to-top-integration.md`) |
| `docs/spec/` | Versioned stage docs |
| `docs/spec/common/records/` | Cross-version governance records |
| `docs/reference/` | External reference materials |

### 8.2 Single Source of Truth (SoT)

`docs/design-v2/01-system/system-baseline.md` is the historical authoritative file for `v0.01 Frozen`; the current mainline follows `docs/spec/v0.01-plus/README.md` and `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`.

### 8.3 Archive Rules

- Stage docs use versioned directories: `docs/spec/<version>/`
- Active execution and archival share the same directory scheme: `docs/spec/<version>/`
- Cross-version governance records live in: `docs/spec/common/records/`
- System design docs live only in: `docs/design-v2/`

---

## 9. Quality Gates

- Commands must run, tests must reproduce, artifacts must be inspectable
- Hardcoded path checks and A-share rule checks
- Effective tests matter more than coverage numbers
- No bare-code-only submissions: key business logic, time rules, and state-machine branches must include necessary comments
- Code delivery must include minimal readable comments plus test or verification evidence
- TODO/HACK/FIXME are allowed during development but must be cleaned before merge

---

## 10. Core Algorithm Constraints

- Current mainline: `Selector preselection -> BOF -> IRS ranking -> MSS position control`
- `MSS` is market-level only; `IRS` is industry-level only; `PAS` is BOF-only on the current mainline
- Each raw observation belongs to exactly one factor
- Modules pass result contracts only

---

## 11. Tech Stack

- Python `>=3.10`
- DuckDB single-database storage
- TuShare (primary) + AKShare (fallback)
- backtrader for calendar stepping/data feed only; in-house Broker for trade semantics
- CLI first, GUI later

---

## 12. Repository Remotes

- `origin`: `${REPO_REMOTE_URL}`
- `backup`: `${REPO_BACKUP_REMOTE_URL}`
- Every remote-sync commit must be pushed to both `origin` and `backup`

---

## 13. Historical Notes

- v0.01 historical baseline: `docs/design-v2/01-system/system-baseline.md`
- Current mainline: `docs/spec/v0.01-plus/README.md`
- Versioned docs entry: `docs/spec/`
- Cross-version records: `docs/spec/common/records/`
- References: `docs/reference/`

---

## 14. Execution Plan

Current execution plan: `docs/spec/v0.01-plus/README.md` and `docs/spec/common/records/development-status.md`; the `v0.01` historical execution plan remains in `docs/design-v2/01-system/system-baseline.md`.

## 15. Git Auth Baseline

- Prefer `openssl` as TLS backend
- Remote-authenticated `git push` should run where credentials are accessible

## 16. MCP Baseline

Recommended MCP services:
- `context`
- `fetch`
- `filesystem`
- `sequential-thinking`
- `mcp-playwright`

Default policy:
- Version-sensitive API/framework issues -> `context`
- Non-rendered web content -> `fetch`
- Non-trivial file I/O -> `filesystem`
- Complex multi-step reasoning -> `sequential-thinking`
- UI flows and replay -> `mcp-playwright`

## 17. Test And Tool Layout Rules (Mandatory)

### 17.1 tests must follow type + module

1. `tests/unit/<module>/`
2. `tests/integration/<module>/`
3. `tests/patches/<module>/`
4. `<module>` must mirror `src/`
5. When changing `src/<module>/`, update tests in the matching module folder

### 17.2 scripts is the only tool entry

1. Non-runtime engineering/ops utilities must live under `scripts/`
2. Classify by domain: `scripts/data/`, `scripts/backtest/`, `scripts/report/`, `scripts/ops/`, etc.
3. `scripts/` tools must not become runtime dependencies for `src/`
4. New tools must go into the matching category folder, never the repository root

