# Backtest Runner Index

**状态**: `Active`  
**日期**: `2026-03-18`

---

## 1. 目录职责

`scripts/backtest/` 是“回测与证据 runner 集合”，不是系统默认入口。

这层脚本的定位是：

1. 运行矩阵回放、ablation、sensitivity、digest、专项归因。
2. 为第一到第三战场生成 evidence。
3. 为 closeout、validation、专项候选裁决提供批处理入口。

这层脚本不是：

1. 日常系统运行入口。
2. 数据日更入口。
3. 主线运行合同本身。

固定入口优先级：

1. 默认系统运行优先走 `main.py` / `eq ...`
2. `scripts/backtest/` 只服务回测、证据和专项验证
3. runner 的结果必须回到对应 card / record 解释，不能反过来单独定义主线

---

## 2. 运行前置

运行任何 backtest runner 之前，固定先满足下面 4 条：

1. 当前 Python 环境为仓库根目录 `.venv`
2. 已执行 `scripts/ops/bootstrap_env.ps1`
3. `.env` 已配置 `DATA_PATH` 与 `TEMP_PATH`
4. 至少通过一轮 smoke 或 preflight

---

## 3. Runner Family

| 前缀/脚本 | 归属 | 正确用途 | 主要输出位置 |
|---|---|---|---|
| `run_v001_plus_*` | 第一战场 / 主线专项 | `v0.01-plus` 的 matrix、ablation、trade attribution、sensitivity | `docs/spec/v0.01-plus/evidence/` |
| `run_normandy_*` | 第二战场 / Normandy | alpha provenance、exit damage、pilot-pack、专项 digest | `normandy/03-execution/evidence/` |
| `run_positioning_*` | 第三战场 / Positioning | sizing / partial-exit family replay、digest、control matrix | `positioning/03-execution/evidence/` |
| `run_phase6_integrated_validation.py` | 第一战场 / Phase 6 | 统一默认系统候选验证 | `docs/spec/v0.01-plus/evidence/` |
| `run_phase9_duration_percentile_validation.py` | 第一战场 / Phase 9B | `duration_percentile` 单变量负向过滤验证 | `docs/spec/v0.01-plus/evidence/` |
| `run_phase9_duration_lifespan_distribution.py` | 第一战场 / Phase 9E | 书义寿命分布重跑，输出 quartile + average lifespan odds evidence | `docs/spec/v0.01-plus/evidence/` |
| `run_closed_loop_fullspan_reports.py` | 报告导出 | 2020-2026 闭环年度报告与逐笔文件 | 仓库外报告目录 |
| `run_mainline_yearly_reports.py` | 报告导出 | 主线逐年摘要报告 | 仓库外报告目录 |
| `check_idempotency.py` | 跨线校验 | 幂等检查，不直接给主线结论 | 对应 evidence 目录 |
| `run_selector_strategy_smoke.py` | 轻量工具 | selector + strategy 最小联调烟测 | 临时输出 |
| `run_mss_baseline_calibration.py` | 历史工具 | MSS 基线校准 | 临时/专项 evidence |
| `run_mss_variant_comparison.py` | 历史工具 | MSS 变体对照 | 临时/专项 evidence |
| `run_week2_*` | 历史工具 | 旧阶段专项分析 | 临时/专项 evidence |

---

## 4. 当前常用脚本

### 4.1 第一战场

| 脚本 | 用途 |
|---|---|
| `run_v001_plus_dtt_matrix.py` | 主线 DTT matrix |
| `run_v001_plus_pas_ablation.py` | PAS ablation |
| `run_v001_plus_irs_ablation.py` | IRS ablation |
| `run_v001_plus_mss_regime_sensitivity.py` | MSS regime sensitivity |
| `run_v001_plus_trade_attribution.py` | trade attribution |
| `run_v001_plus_windowed_sensitivity.py` | windowed sensitivity |
| `run_v001_plus_rank_decomposition.py` | rank decomposition |
| `run_phase6_integrated_validation.py` | Phase 6 integrated validation |
| `run_phase9_duration_percentile_validation.py` | Phase 9B duration_percentile isolated validation |
| `run_phase9_duration_lifespan_distribution.py` | Phase 9E 书义寿命分布重跑 |

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

1. 不把 `scripts/backtest/` 当作系统唯一入口。
2. 不拿某一个 runner 的单次结果直接宣布默认参数变更。
3. 不跳过对应的 card / record 单独解释 evidence。
4. 不把历史 runner 误认成当前 canonical runner。

---

## 6. 一句话结论

`scripts/backtest/` 是“研究、验证、证据 runner 层”，不是系统默认运行层。
