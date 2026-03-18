# GX8 Evidence: 三层趋势层级重构
**状态**: `Completed`
**日期**: `2026-03-19`

---

## 1. 代码证据

本轮直接落到的代码文件：

1. [`../../../src/selector/gene.py`](../../../src/selector/gene.py)
2. [`../../../src/data/store.py`](../../../src/data/store.py)
3. [`../../../tests/unit/selector/test_gene.py`](../../../tests/unit/selector/test_gene.py)

---

## 2. 真实实现证据

### 2.1 wave ledger 已三层化

`gene.py` 现在会按层级分别构建：

1. `SHORT`
2. `INTERMEDIATE`
3. `LONG`

并把三层 wave 一起写入 `l3_gene_wave`。

### 2.2 父趋势参照已分层写实

当前正式 basis 已变成：

1. `SHORT_PARENT_CONTEXT_DIRECTION`
2. `INTERMEDIATE_PARENT_CONTEXT_DIRECTION`
3. `LONG_SELF_DIRECTION_BOOTSTRAP`

这意味着 `wave_role` 不再只是假装“有父趋势”，而是能明确回答自己相对于哪一层。

### 2.3 active snapshot 已三层暴露

`l3_stock_gene` 已新增：

1. `current_short_*`
2. `current_intermediate_*`
3. `current_long_*`

这些字段把三层 active wave 的：

1. `trend_level`
2. `context_trend_level`
3. `context_trend_direction`
4. `wave_role`
5. `wave_role_basis`
6. `two_b_window_*`

正式暴露给下游。

### 2.4 canonical 中层视图被保留

这轮没有偷偷改写已有第一战场结果对应的 canonical 字段。

正式口径是：

1. 旧 `current_*` 继续服务当前 `INTERMEDIATE proxy` 验证链
2. 新三层 hierarchy 通过显式新字段提供
3. 因此 `GX8` 已完成，但不会静默篡改此前 `Phase 9B` 的 proxy 结论

---

## 3. schema 证据

`store.py` 已把 schema 升到：

`v15`

新增三层 snapshot 字段组，每层包含：

1. `trend_level`
2. `wave_id`
3. `wave_direction`
4. `context_trend_level`
5. `context_trend_direction`
6. `wave_role`
7. `wave_role_basis`
8. `two_b_window_bars`
9. `two_b_window_basis`
10. `wave_start_date`
11. `wave_age_trade_days`

---

## 4. 单测证据

新增并通过的关键断言：

1. `test_compute_gene_writes_gx8_three_level_hierarchy`
2. `l3_gene_wave` 真实出现 `SHORT / INTERMEDIATE / LONG`
3. `SHORT -> INTERMEDIATE parent`
4. `INTERMEDIATE -> LONG parent`
5. `LONG -> LONG self bootstrap`
6. `SHORT / INTERMEDIATE / LONG` 的 `2B` 窗口分别为 `1 / 5 / 10`

---

## 5. 验证命令

已通过：

```bash
python -m pytest tests/unit/selector/test_gene.py -q
```

以及：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile hook
```

---

## 6. 证据结论

`GX8` 现在已经不再只是“准备开工”的概念卡，而是有了真实代码、真实 schema、真实测试和真实状态同步的完整证据闭环。  
它解决的不是数值优劣，而是第四战场最后一块层级语义定义债。
