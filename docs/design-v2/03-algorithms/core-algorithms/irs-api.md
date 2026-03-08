# IRS 接口契约设计

**版本**: `v0.01-plus IRS-lite + IRS-upgrade 设计骨架`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在保持当前主线输入输出边界不变的前提下，补充升级版接口草案。`  
**上游文档**: `irs-algorithm.md`, `irs-data-models.md`

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容附录。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的接口整理结果，不再构成仓库现行设计权威。现行 `IRS-lite` 正文以 `blueprint/01-full-design/05-irs-lite-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 当前主线接口

### 1.1 计算入口

当前主线对应实现：

- `src/selector/irs.py::compute_irs`

当前语义：

1. 输入行业日线和基准指数
2. 产出行业日分与行业排名
3. 写入 `l3_irs_daily`

### 1.2 当前输入

| 输入 | 来源 | 说明 |
|---|---|---|
| `store` | `Store` | DuckDB 访问句柄 |
| `start` | `date` | 开始日期 |
| `end` | `date` | 结束日期 |
| `baseline` | `dict | None` | 标准化参数 |
| `min_industries_per_day` | `int` | 最小有效行业数 |

### 1.3 当前输出

| 输出 | 类型 | 说明 |
|---|---|---|
| 返回值 | `int` | 写入行数 |
| 落库表 | `l3_irs_daily` | 行业评分结果表 |

### 1.4 当前异常语义

| 场景 | 当前行为 |
|---|---|
| `l2_industry_daily` 空 | 返回 `0` |
| 当日行业数不足 | 跳过当日 |
| 基准缺失 | 基准涨跌幅按 `0` 处理 |
| 行业缺失 | 运行时过滤 `未知` |

## 2. 当前主线消费接口

### 2.1 `Strategy / Ranker`

当前消费者：

- `src/strategy/ranker.py`

当前消费字段：

1. `industry`
2. `score`
3. `rank`

当前使用方式：

1. `BOF` 触发后，根据股票所属行业读取 `score`
2. 缺失时按 `50` 中性分 fallback
3. 把 `irs_score` 带入 `final_score`

### 2.2 非消费者

当前明确不消费 `IRS` 的模块：

1. `Selector`
2. `Broker / Risk`
3. `Report` 的正式实时主链

## 3. 升级版接口草案

若进入 `IRS-upgrade`，建议拆成两层接口。

### 3.1 行业轮动层

建议入口：

```python
compute_irs_rotation(
    store: Store,
    start: date,
    end: date,
) -> int
```

建议输出：

1. `rotation_status`
2. `rotation_slope`
3. `continuity_score`
4. `diffusion_score`

### 3.2 牛股基因层

建议入口：

```python
compute_irs_gene_overlay(
    store: Store,
    start: date,
    end: date,
) -> int
```

建议输出：

1. `leader_score`
2. `gene_score`
3. `bof_hit_density`
4. `strong_stock_ratio`

## 4. 当前接口约束

1. 当前主线不把 `IRS` 重新拉回 `Selector`
2. 当前主线不允许 `IRS` 直接变成硬过滤器
3. 升级版接口可以扩字段，但不能改变：
   - `Selector 初选 -> BOF -> IRS 排序 -> MSS 控仓位`
   这条主线边界
