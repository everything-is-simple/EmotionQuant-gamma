# WARP.en.md

This file provides minimal, executable repository rules for automated agents. Content is equivalent to `AGENTS.md`, `CLAUDE.md`, `CLAUDE.en.md`, `WARP.md`, and `WARP.en.md`, targeting generic agent runtimes.

**Document Version**: `v0.01 Formal Release`  
**Document Status**: `Frozen`  
**Freeze Date**: `2026-03-03`  
**Change Policy**: Only errata, link fixes, and non-semantic formatting updates are allowed; execution semantics must not change.

---

## 1. Document Positioning

- Purpose: minimal, executable repository rules for automated agents.
- **Authoritative design entry**: `docs/design-v2/system-baseline.md` (rebuild design document, single source of truth)
- Stage documents are archived under `docs/spec/`; reference materials are under `docs/reference/`

---

## 2. System Positioning

EmotionQuant is a sentiment-driven quantitative system for China A-shares.

- Solo developer project
- Execution model: **4-week incremental delivery** (each week produces independently verifiable deliverables)
- Docs serve implementation — no "docs perfection" pursuit

---

## 3. Iron Laws (v0.01)

1. **v0.01 live scope = BOF single-pattern closed loop**; MSS/IRS are optional funnel gates and must pass ablation before being enabled.
2. **MSS only looks at market level** — never touches industry or individual stocks.
3. **IRS only looks at industry level** — never touches market temperature or stock patterns.
4. **PAS is a framework-level concept; v0.01 implementation is BOF only**, and does not take MSS/IRS scores as pattern inputs.
5. **Each raw observation belongs to exactly one factor** — no cross-factor double counting.
6. **Modules only pass "result contracts"** (pydantic objects) — no internal intermediate features.
7. **Each module can be unit-tested independently** — no dependency on other modules to start.
8. **Backtest and paper trading share the same broker kernel**.
9. **No hardcoded paths/secrets** — all injected via config.py.
10. **Execution semantics fixed to T+1 Open**: signal_date=T, execute_date=T+1, fill price=T+1 Open.

Details: `docs/design-v2/system-baseline.md` (current version is authoritative).

---

## 4. Development Flow

- Execution model: 4-week incremental delivery (see current system-baseline.md).
- Each week produces independently verifiable deliverables (runnable code + passing tests)
- Branch naming: `rebuild/{module}`, merge target `main`

---

## 5. Data Contracts

Inter-module data passed as pydantic objects (contracts.py):
- `MarketScore` (MSS → Selector)
- `IndustryScore` (IRS → Selector)
- `StockCandidate` (Selector → Strategy)
- `Signal` (Strategy → Broker)
- `Order` / `Trade` (Broker internal → Report)

Code in English, comments/docs/UI in Chinese. Uniform `snake_case`.
L1 layer uses `ts_code` (TuShare format), L2+ layers use `code` (6-digit pure code).

Details: `docs/design-v2/system-baseline.md` (result-contract section).

---

## 6. Data Architecture

DuckDB single-database storage, decoupled via L1-L4 layers. Data root injected via `DATA_PATH` environment variable (directory outside repo).

| Layer | Content |
|-------|---------|
| L1 | Raw data (API fetch, written by fetcher.py) |
| L2 | Processed data (adjusted prices / moving averages / volume ratio / market snapshot / industry daily) |
| L3 | Algorithm output (MSS / IRS / PAS(BOF) / Gene analysis) |
| L4 | Historical analysis cache (orders / trades / reports) |

**Dependency rule**: L2 reads only L1; L3 reads only L1/L2; L4 reads only L1/L2/L3. Reverse dependencies forbidden.

Details: `docs/design-v2/system-baseline.md` (data and boundary sections).

---

## 7. Architecture (6 Modules)

| Module | Responsibility |
|--------|---------------|
| Data | Fetch, clean, store, cache algorithm output |
| Selector | MSS market sentiment + IRS industry rotation → candidate pool (Gene is post-analysis only) |
| Strategy | PAS pattern detection (v0.01 BOF only) → trade signals |
| Broker | Risk control + matching (backtest and paper trading share kernel) |
| Backtest | Historical backtesting (backtrader single engine; clock/data-feed only, trading kernel is in-house Broker) |
| Report | Backtest reports + daily stock selection reports + alerts |

---

## 8. Governance Structure

### 8.1 Directory Positioning

| Directory | Role |
|-----------|------|
| `docs/design-v2/` | System-level design documents (system-baseline.md is sole authoritative entry) |
| `docs/spec/` | Stage archives (v0.01+; roadmap/spec/runbook/errata/release notes) |
| `docs/reference/` | Reference and external methodology materials (non-execution source) |
| `.kiro/roadmap/` | Active stage working set (versioned subdirectories) |

### 8.2 Single Source of Truth (SoT)

`docs/design-v2/system-baseline.md` is the sole authoritative design document (current version/sections prevail).

### 8.3 Archive Rules

- Stage documents are archived by version under: `docs/spec/<version>/`
- Active-stage working copies are maintained under: `.kiro/roadmap/<version>/`
- System-level design documents are stored only in: `docs/design-v2/`

---

## 9. Quality Gates

- Commands must run, tests must reproduce, artifacts must be verifiable
- Hardcoded path checks, A-share rule checks
- Effective tests over coverage numbers
- No "bare code only" submissions: key business logic, time-semantics rules, and state-machine branches must include necessary comments (intent, boundary, constraints) for maintainability
- Code delivery must include both: minimal readable comments + corresponding test/verification evidence (at least one traceable to a test case or regression record)
- TODO/HACK/FIXME: allowed during development, must be cleaned before merge

---

## 10. Core Algorithm Constraints

- v0.01 live scope: BOF single-pattern closed loop; MSS/IRS are optional gates enabled only after ablation
- MSS only at market level, IRS only at industry level; PAS is a framework concept and v0.01 uses BOF only
- Each raw observation belongs to exactly one factor — no cross-factor double counting
- Modules only pass "result contracts" (pydantic objects) — no internal intermediate features

Details: `docs/design-v2/system-baseline.md` (iron laws, module boundaries, trigger sections).

---

## 11. Tech Stack

- Python `>=3.10`
- Storage: DuckDB single database
- Data sources: TuShare (primary) + AKShare (fallback)
- Backtesting: backtrader single engine (clock/data-feed only, trading kernel is in-house Broker)
- GUI: CLI only for MVP, GUI deferred

Details: `docs/design-v2/system-baseline.md` (current version).

---

## 12. Repository Remotes

- `origin`: `${REPO_REMOTE_URL}` (defined in `.env.example`; current value: `https://github.com/everything-is-simple/EmotionQuant-gamma`)
- `backup`: `${REPO_BACKUP_REMOTE_URL}` (defined in `.env.example`; current value: `https://gitee.com/wangweiyun2233/EmotionQuant-gamma`; suggested local remote name `backup`)
- Push policy: every commit intended for remote sync must be pushed to both `origin` and `backup`; single-remote push is not acceptable.

---

## 13. Historical Notes

System baseline authoritative entry: `docs/design-v2/system-baseline.md`
Stage full archives: `docs/spec/`
Active-stage working set: `.kiro/roadmap/`
Reference materials: `docs/reference/`

---

## 14. Execution Plan

Current execution plan: see `docs/design-v2/system-baseline.md` (current version).

## 15. Git Auth Baseline

- TLS backend baseline: prefer `openssl` (`git config --global http.sslbackend openssl`, repo-level override allowed).
- In restricted sandbox sessions, authenticated `git push` should run in non-sandbox or elevated mode to ensure credential interaction and storage paths are accessible.

## 16. MCP Baseline

Recommended MCP services:
- `context` (Context7 document/context retrieval)
- `fetch` (HTTP content fetching)
- `filesystem` (cross-directory file operations)
- `sequential-thinking` (multi-step reasoning)
- `mcp-playwright` (browser automation)

Skill vs MCP boundary:
- Skill = process instructions / templates.
- MCP = runtime tools.
- Skills do not replace MCP.

Default trigger policy:
- Version-sensitive API/framework issues → prefer `context`.
- Non-browser-rendered web content → prefer `fetch`.
- Non-trivial file I/O → prefer `filesystem`.
- Multi-branch decisions and complex troubleshooting → prefer `sequential-thinking`.
- UI flows and screenshot replay → prefer `mcp-playwright`.

Bootstrap:
- One-click: `powershell -ExecutionPolicy Bypass -File scripts/setup/bootstrap_dev_tooling.ps1`
- MCP only: `powershell -ExecutionPolicy Bypass -File scripts/setup/configure_mcp.ps1 -ContextApiKey <your_key>`
- Optional MCP target dir: `-CodexHome <path>` (default: in-project `.tmp/codex-home`)
- Hooks only: `powershell -ExecutionPolicy Bypass -File scripts/setup/configure_git_hooks.ps1`
- Skills check only: `powershell -ExecutionPolicy Bypass -File scripts/setup/check_skills.ps1`







## 17. Test And Tool Layout Rules (Mandatory)

### 17.1 tests must follow "type + module"

1. `tests/unit/<module>/`: unit tests (pure function / single module)
2. `tests/integration/<module>/`: integration tests (cross-module flow)
3. `tests/patches/<module>/`: patch/regression tests (prevent known bug rollback)
4. `<module>` must mirror `src/`: `data/selector/strategy/broker/backtest/report/core`
5. When changing `src/<module>/`, add/update tests in the matching module folder; do not drop tests at tests root

### 17.2 scripts is the only tool entry

1. Any non-runtime but required engineering/ops utility must live under `scripts/`
2. Classify by domain: `scripts/data/`, `scripts/backtest/`, `scripts/report/`, `scripts/ops/`, etc.
3. Tools under `scripts/` must not become runtime dependencies for `src/`
4. New tools must be placed in the matching category folder, never at repository root
