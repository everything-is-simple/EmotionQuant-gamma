# Current System Usage Map

**状态**: `Active`  
**日期**: `2026-03-19`  
**定位**: `一页看清当前系统怎么用、四个目录各放什么、Gene 平均寿命框架怎么读`

---

## 1. 这页回答什么

如果你现在只想快速搞清 3 件事，就先看这一页：

1. 系统的 `4` 个根目录各自负责什么
2. 当前主线到底该先看哪些文档，不必在仓库里乱翻
3. Gene 的“平均寿命框架”已经落到了哪里，以及现在该怎么用

---

## 2. 四目录纪律

当前系统固定按下面 `4` 个根目录分工：

| 根目录 | 职责 | 允许放什么 | 不允许放什么 |
|---|---|---|---|
| `G:\EmotionQuant-gamma` | 代码与正式治理仓库 | `src/`、`tests/`、`docs/`、`blueprint/`、脚本、formal evidence、formal record | working DB、pytest 临时目录、回测副本、临时缓存 |
| `G:\EmotionQuant_data` | 正式数据根 | 正式执行库、旧库候选、长期日志、长期数据产物 | 源码、临时实验输出、一次性工作副本 |
| `G:\EmotionQuant-temp` | 临时运行根 | working DB、pytest/backtest 副本、临时 artifacts、缓存、中间产物 | 正式 SoT 文档、长期报表归档、需要进 Git 的结果 |
| `G:\EmotionQuant-report` | 人读报告根 | 年报、闭环报告、导出表、给人看的长报告产物 | working DB、临时缓存、formal 治理证据 |

最重要的边界只有一句话：

`formal truth 留在仓库；正式数据留在 data；临时运行留在 temp；给人看的导出报告留在 report。`

---

## 3. 常见产物放哪

1. `blueprint card / record / docs/spec evidence JSON` 放 `G:\EmotionQuant-gamma`
2. 正式执行库 `emotionquant.duckdb` 放 `G:\EmotionQuant_data`
3. backtest working copy、pytest cache、实验 DuckDB 放 `G:\EmotionQuant-temp`
4. `run_mainline_yearly_reports.py`、`run_closed_loop_fullspan_reports.py` 这类长报告导出默认放 `G:\EmotionQuant-report`

也就是说：

1. `report` 不是 formal evidence 根
2. `temp` 不是长期报告归档根
3. `gamma` 不是临时运行盘

---

## 4. 现在先看哪些文档

如果你只想按当前主线口径工作，阅读顺序固定为：

1. [`../../../README.md`](../../../README.md)
2. [`../../../blueprint/README.md`](../../../blueprint/README.md)
3. [`../../../blueprint/03-execution/00-current-dev-data-baseline-20260311.md`](../../../blueprint/03-execution/00-current-dev-data-baseline-20260311.md)
4. [`../../../blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`](../../../blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md)
5. [`current-mainline-operating-runbook-20260317.md`](./current-mainline-operating-runbook-20260317.md)

如果你只想配环境，而不是理解主线治理，再看：

1. [`setup-guide.md`](./setup-guide.md)

---

## 5. Gene 平均寿命框架是什么

它不是一句抽象口号，而是系统里正式存在的一组读数：

1. `current_wave_magnitude_remaining_prob`
2. `current_wave_duration_remaining_prob`
3. `current_wave_lifespan_average_remaining_prob`
4. `current_wave_lifespan_average_aged_prob`
5. `current_wave_lifespan_remaining_vs_aged_odds`
6. `current_wave_lifespan_aged_vs_remaining_odds`

它回答的是：

1. 当前中级主要走势从“幅度”看，还剩多少路
2. 从“时间”看，还剩多少路
3. 把幅度和时间合并后，这段波更像“还有余量”还是“已经老化”

这些读数已经正式落在：

1. `l3_stock_gene`
2. `l3_gene_wave`
3. `l3_gene_distribution_eval`

对应实现见：

1. [`../../../src/selector/gene.py`](../../../src/selector/gene.py)
2. [`../../../src/data/store.py`](../../../src/data/store.py)

---

## 6. 平均寿命框架现在怎么用

当前正确用法是：

1. 当作 `Gene sidecar / attribution / distribution reading`
2. 在 signal date 上读 quartile、joint percentile、average aged/remaining odds
3. 在 backtest / validation 里看这些 bucket 的收益、胜率、持有期是否稳定恶化

当前不正确的用法是：

1. 直接把它当默认 runtime hard gate
2. 因为 isolated round 以前赢过，就继续拿旧 `p65 / p95` 阈值当真理
3. 在 joint quartile 样本不够时，口头宣布某个寿命阈值已可推广

`2026-03-19` 的正式状态已经被 `17.8 / Phase 9E` 写死：

1. 平均寿命框架已经落地到 Gene
2. 但当前证据只支持它留在 sidecar
3. 不支持把 duration 再直接带进 `Phase 9F` runtime combination replay

对应 formal record：

1. [`../../../blueprint/03-execution/records/phase-9e-duration-lifespan-distribution-record-20260319.md`](../../../blueprint/03-execution/records/phase-9e-duration-lifespan-distribution-record-20260319.md)

---

## 7. 一句话基线

`当前系统是四目录分治：gamma 管代码与正式治理，data 管正式数据，temp 管临时运行，report 管人读报告；Gene 平均寿命框架已经进入系统，但当前仍属于 sidecar 解释层，而不是默认 runtime gate。`
