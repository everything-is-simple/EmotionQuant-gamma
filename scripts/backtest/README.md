# Backtest Runner Index

**状态**: `Active`  
**日期**: `2026-03-15`

---

## 1. 用途

本文只做一件事：

`给 scripts/backtest/ 提供最小 runner 索引，避免把研究脚本误当系统默认入口。`

固定入口优先级：

1. 日常系统运行优先走 `python main.py ...` 或 `eq ...`
2. `scripts/backtest/` 只服务回测、证据、研究矩阵与专项归因
3. 研究脚本不得反向定义主线默认口径

---

## 2. 固定主环境前提

运行任何 backtest runner 之前，固定先满足下面 4 条：

1. 当前唯一 Python 环境 = 仓库根目录 `.venv`
2. 已执行 `scripts/ops/bootstrap_env.ps1`
3. `.env` 已配置 `DATA_PATH` 与 `TEMP_PATH`
4. 先通过最小 smoke：
   - `python -m pytest -m smoke -q`

---

## 3. Runner Family Index

| 脚本/前缀 | 归属 | 正确用途 | 主要产物落点 |
|---|---|---|---|
| `run_v001_plus_*` | 第一战场 / 主线专项 evidence | 主线 `v0.01-plus` 的 matrix、ablation、trade attribution、windowed sensitivity、regime sensitivity | `docs/spec/v0.01-plus/evidence/` |
| `run_normandy_*` | 第二战场 / Normandy | alpha provenance、exit damage、Tachibana pilot-pack 等研究矩阵与 digest | `normandy/03-execution/evidence/` |
| `run_positioning_*` | 第三战场 / Positioning | sizing / partial-exit 的 family replay、digest、control matrix | `positioning/03-execution/evidence/` |
| `check_idempotency.py` | 跨线校验 | 幂等检查，不负责主线/研究线结论裁决 | 对应战役 evidence 目录 |
| `run_selector_strategy_smoke.py` | 轻量工具 | selector + strategy 的最小烟测，不替代正式 backtest | 临时控制台输出 / 临时产物 |
| `run_mss_baseline_calibration.py` | 主线历史工具 | MSS baseline 校准 | 临时/专项 evidence |
| `run_mss_variant_comparison.py` | 主线历史工具 | MSS variant 对照 | 临时/专项 evidence |
| `run_week2_*` | 旧阶段专项工具 | 旧阶段周任务分析，不作为当前主线默认入口 | 临时/专项 evidence |

---

## 4. 当前常用 Runner

### 4.1 主线

| 脚本 | 用途 |
|---|---|
| `run_v001_plus_dtt_matrix.py` | 主线 DTT matrix 总入口 |
| `run_v001_plus_pas_ablation.py` | PAS 专项消融 |
| `run_v001_plus_irs_ablation.py` | IRS 专项消融 |
| `run_v001_plus_mss_regime_sensitivity.py` | MSS regime sensitivity |
| `run_v001_plus_trade_attribution.py` | 主线 trade attribution |
| `run_v001_plus_windowed_sensitivity.py` | 主线窗口敏感性 |
| `run_v001_plus_rank_decomposition.py` | 主线 rank decomposition |

### 4.2 第二战场

| 脚本 | 用途 |
|---|---|
| `run_normandy_bof_control_exit_matrix.py` | BOF control exit matrix |
| `run_normandy_bof_control_exit_digest.py` | BOF control exit digest |
| `run_normandy_bof_control_trailing_stop_followup.py` | trailing-stop follow-up |
| `run_normandy_tachibana_pilot_pack_matrix.py` | Tachibana pilot-pack matrix |
| `run_normandy_tachibana_pilot_pack_digest.py` | Tachibana pilot-pack digest |

### 4.3 第三战场

| 脚本 | 用途 |
|---|---|
| `run_positioning_null_control_matrix.py` | sizing lane null control |
| `run_positioning_sizing_family_matrix.py` | sizing family replay |
| `run_positioning_single_lot_sanity_matrix.py` | single-lot sanity |
| `run_positioning_partial_exit_null_control_matrix.py` | partial-exit null control |
| `run_positioning_partial_exit_family_matrix.py` | partial-exit family replay |
| `run_positioning_partial_exit_family_digest.py` | partial-exit family digest |

---

## 5. 不该怎么用

1. 不把 `scripts/backtest/` 里的 runner 当作“主系统唯一入口”
2. 不直接挑一个研究脚本跑完就宣布默认参数变更
3. 不跳过对应战役 card / record 去单独解释 evidence
4. 不把旧阶段专项工具误当当前主线 canonical runner

---

## 6. 一句话结论

`scripts/backtest/` 是研究与证据工具层，不是系统默认入口层；先认主线入口，再按战役选择对应 runner family。
