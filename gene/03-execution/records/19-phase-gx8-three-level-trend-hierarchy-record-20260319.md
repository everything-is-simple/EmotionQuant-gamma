# GX8 Record: 三层趋势层级重构
**状态**: `Completed`
**日期**: `2026-03-19`

---

## 1. 记录目的

这份 record 只记录三件事：

1. `GX8` 到底解决了什么
2. 这轮为什么要保留 canonical 中层兼容视图
3. `GX8` 完成后，第一战场的真实下一步是什么

---

## 2. 本轮正式结论

### 2.1 `trend_level` 三层并存已正式实现

当前第四战场已经不再只有：

`INTERMEDIATE`

而是正式拥有：

1. `SHORT`
2. `INTERMEDIATE`
3. `LONG`

三层 wave ledger。

### 2.2 `mainstream / countertrend` 已能回答父层问题

当前正式口径已经从“只有中层 proxy”推进到：

1. `SHORT` 相对于 `INTERMEDIATE`
2. `INTERMEDIATE` 相对于 `LONG`
3. `LONG` 用 `self bootstrap` 明确写实

因此现在已经可以诚实回答：

`这段 wave 的主流/逆流，到底是相对于哪一层父趋势。`

### 2.3 `2B` 的层级窗口现在和 hierarchy 同步

当前正式写定为：

1. `SHORT -> 1`
2. `INTERMEDIATE -> 5`
3. `LONG -> 10`

这让 `wave ledger` 的层级语义和 `2B` 窗口不再脱节。

---

## 3. 为什么本轮保留 canonical 中层兼容视图

如果这轮直接把已有 `l3_stock_gene` canonical 字段整体改成三层新语义，会带来一个不诚实的问题：

`前面 Phase 9B 已经收口的 proxy isolated validation，会被静默改口径。`

因此本轮正式采取的策略是：

1. `wave ledger` 直接完成真三层
2. `snapshot` 新增显式三层字段组
3. 旧 canonical 字段继续保留中层 proxy 口径

这不是退让，而是治理纪律：

`先把 hierarchy 做真，再决定第一战场何时切换消费口径。`

---

## 4. 对第一战场的影响

`GX8` 完成后，之前那个硬门槛已经真实解除：

1. `Phase 9C` 不再受 `GX8` 阻塞
2. `Phase 9D` 的外部 hierarchy gate 也已满足

但这不等于 `Gene` 已经包级升格完成。  
它只意味着：

`第一战场现在终于可以诚实进入组合候选，而不是继续拿 GX8 当借口卡住。`

---

## 5. 下一步

当前最自然、也最诚实的下一步是：

[`../../../blueprint/03-execution/17.6-phase-9c-formal-combination-freeze-card-20260318.md`](../../../blueprint/03-execution/17.6-phase-9c-formal-combination-freeze-card-20260318.md)

也就是：

1. 先写 formal combination freeze
2. 只从已经赢下 isolated round 的字段里选组合候选
3. 不偷带 `wave_role / age_band / mirror / conditioning / gene_score`

---

## 6. 一句话收口

`GX8` 现在已经把第四战场从“趋势层级还是单层 proxy”推进到了“wave 真三层、snapshot 真三层暴露、第一战场仍保留中层兼容视图”的正式状态；因此它不再是 Phase 9C / 9D 的 blocker。`
