# Tachibana Contrary Alpha Search Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `Normandy / N1.8 Tachibana contrary alpha search`

---

## 1. 定位

本文不是把 `立花义正` 直接改写成当前主线 `PAS` 或 `MSS`。

`N1.8` 只回答一个问题：

`立花义正理论里最可执行的那条“极端一致失效”链，能不能在 A 股日线 / T+1 Open 语义下形成独立 alpha。`

这轮不试图一次性复刻全部 `立花义正交易法`，而是先从最像 entry alpha 的核心假设切一刀。

---

## 2. 当前已知前提

截至 `2026-03-12`，下面这些前提已经固定：

1. `BOF` 继续是当前 `Normandy` 的固定 baseline / control
2. `Tachibana` 当前被定义为：
   - `contrary doctrine`
   - `crowd-extreme observation framework`
   - `execution / risk rhythm discipline`
3. `Tachibana` 不属于当前 `PAS` taxonomy
4. `Tachibana` 研究当前仍未有 formal detector，也没有任何正式 backtest evidence

因此 `N1.8` 的第一原则是：

`先把立花理论缩成一个最小可执行假设，再谈回测。`

---

## 3. 当前固定的第一可执行假设

`N1.8` 当前固定只测试一个最小 entry 假设：

`TACHI_CROWD_FAILURE`

它的理论语义不是“逢反向就做”，而是：

1. 市场大众已经明显站到一边
2. 价格继续沿一致方向推进到极端
3. 推进开始失效，出现一致预期松动
4. 反方向开始出现 first reclaim / failure evidence

一句话压缩：

`先有 crowd extreme，再有 crowd failure。`

---

## 4. 当前要回答的四个问题

`N1.8` 固定只回答四个问题：

1. `TACHI_CROWD_FAILURE` 是否能形成正向 standalone alpha
2. 它和 `BOF` 是高度重叠，还是一条不同的 alpha 链
3. 它的 edge 若存在，更像 entry edge 还是更依赖执行纪律
4. 这条线下一步应进入：
   - 深一层 detector refinement
   - controlled exit decomposition
   - 还是直接 `no-go`

---

## 5. 当前实验允许做什么

当前实验固定允许：

1. 参考 `normandy/01-full-design/90-research-assets/tachibana-yoshimasa-analysis.md`
2. 结合本地原始资料抽取最小 formal contract
3. 在统一长窗口上比较：
   - `BOF_CONTROL`
   - `TACHI_CROWD_FAILURE`
4. 输出 matrix / digest / overlap / incremental 结论

当前实验固定不允许：

1. 把 `Tachibana` 直接塞进 `PAS registry`
2. 一次性 formalize 全套 `试单 / 加减仓 / 休息纪律`
3. 把主观 tape-reading 细节伪装成已经 formalized 的日线规则
4. 在没有最小 detector 之前先报“回测结果”

---

## 6. 当前证据要求

`N1.8` 至少要留下下面这些 evidence：

1. `tachibana_minimal_contract_note`
2. `tachibana_alpha_matrix`
3. `tachibana_alpha_digest`
4. 一份正式 record

其中 `matrix` 至少要覆盖：

1. `trade_count`
2. `EV`
3. `PF`
4. `MDD`
5. `participation`
6. `overlap_with_bof`
7. `incremental_trades_vs_bof`

---

## 7. 当前最小 detector 边界

第一轮 `TACHI_CROWD_FAILURE` detector 当前应尽量只使用日线可复核对象，例如：

1. 连续推进后的极端位置
2. 异常放量或情绪放大代理
3. 推进失败后的回收 / reclaim
4. 清晰的失效点

第一轮当前不强行引入：

1. 盘中 tape
2. 主观盘口语言
3. 融券锁单
4. 完整仓位管理节奏

这些都更适合第二层研究。

---

## 8. 出场条件

`N1.8` 只有在以下条件之一满足时才允许出场：

1. `TACHI_CROWD_FAILURE` 已证明值得继续深挖
2. `TACHI_CROWD_FAILURE` 已证明当前不成立或过度重叠于 `BOF`

无论哪种结果，都必须留下正式 record。

---

## 9. 当前一句话方案

`以 BOF_CONTROL 为固定尺子，把立花义正方法先缩成 TACHI_CROWD_FAILURE 这一条最小可执行假设，先问它有没有 alpha，再问它值不值得继续 formalize。`
