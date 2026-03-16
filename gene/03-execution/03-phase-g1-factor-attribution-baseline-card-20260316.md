# G1 卡: 三子因子解释力基线

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

第四战场第一次正式进入研究层，回答一个问题：

`magnitude / duration / extreme_density` 这三个子因子，到底谁对后续延续或衰竭更有解释力？`

---

## 2. 本卡范围

1. 新建 `l3_gene_factor_eval` 研究表
2. 固定 `G1` 最小基线口径
3. 基于 completed wave 计算固定 horizon 的 forward outcome
4. 输出三子因子的分箱解释力读数
5. 为后续 `G2 / G3 / G6` 提供排序依据

---

## 3. 输入

1. `l2_stock_adj_daily`
2. `l3_gene_wave`
3. `l3_stock_gene`
4. 当前 `compute_gene()` 生成的 completed wave 结构

---

## 4. 固定口径

1. 因子仅允许：
   - `magnitude`
   - `duration`
   - `extreme_density`
2. 样本口径：
   - `SELF_HISTORY_PERCENTILE`
3. 分箱：
   - `P0_20 / P20_40 / P40_60 / P60_80 / P80_100`
4. forward horizon：
   - `10` 个交易日
5. 输出指标：
   - `continuation_rate`
   - `reversal_rate`
   - `median_forward_return`
   - `median_forward_drawdown`
   - `monotonicity_score`

---

## 5. 输出物

1. `l3_gene_factor_eval`
2. `compute_gene()` 追加 `G1` 研究层回写
3. 单元测试：
   - Gene 研究表落库
   - Store schema 创建
   - builder 不破坏 Gene 主窗口语义
4. 第一份真实因子排序读数

---

## 6. 完成标准

1. 每次 `compute_gene()` 在窗口结束日都能产出一张 `factor_eval` 表
2. 三个因子都能输出 `ALL + 五档分箱` 的解释力读数
3. 至少能从主库结果里读出三子因子第一版强弱顺序
4. 不引入新因子，不改实时漏斗，不碰 `Normandy / Positioning`

---

## 7. 结案结论

本卡已完成。  
当前主库第一份真实读数已经落表，且足以给出第一版排序判断：

1. `magnitude` 明显最硬，但方向是“越大越衰竭”
2. `duration` 与 `extreme_density` 目前都弱，二三名尚不稳定

---

## 8. 明确不做

1. 不在本卡做 `65 / 95` 校准
2. 不在本卡重写 `1-2-3 / 2B`
3. 不在本卡把读数硬接成交易过滤器
