# IRS 算法设计

**版本**: v0.01 正式版  
**创建日期**: 2026-03-06  
**状态**: Active（算法级 SoT，执行语义仍受 `system-baseline.md` 冻结约束）  
**变更规则**: 允许在不改变 v0.01 执行语义前提下，对行业分类口径、算法细案与证据回写做受控纠偏。  
**对应模块**: `src/selector/irs.py`, `src/selector/selector.py`, `src/data/cleaner.py`  
**上游文档**: `system-baseline.md`, `selector-design.md`, `architecture-master.md`

---

## 1. 定位

在 v0.01 中，IRS 的职责是：

`给 Selector 提供行业相对优先级。`

它不负责：

- 判断市场该不该做
- 判断个股今天买不买
- 直接输出交易动作

---

## 2. 正式行业口径

自 `2026-03-06` 起，v0.01 正式行业口径固定为：

`SW2021 一级 31 行业`

运行时优先级为：

1. `l1_sw_industry_member`
2. `l1_stock_info.industry`（兼容兜底）

解释：

- `stock_basic.industry` 不是申万一级事实源
- 只有 `index_classify + index_member` 链路才是当前系统认可的正式行业口径

---

## 3. 输入与数据边界

IRS 当前读取：

- `l2_industry_daily`
- `l1_index_daily`（基准：`000001.SH`）

`l2_industry_daily` 的正式生成方式为：

- 先按 `l1_sw_industry_member` 确定个股所属申万一级行业
- 再把个股日线聚合到行业日线
- 非交易日不进入 `L2/L3`

---

## 4. 当前算法定义

### 4.1 两因子

当前 v0.01 只保留两因子：

1. `RS` 相对强度
   `industry_pct_chg - benchmark_pct_chg`
2. `CF` 资金流向
   `flow_share + amount_delta_10d`

### 4.2 权重

- `RS = 55%`
- `CF = 45%`

综合得分：

```text
total_score = 0.55 * rs_score + 0.45 * cf_score
```

### 4.3 排名规则

当前排序固定为：

1. 按 `score` 降序
2. 若分数相同，按 `industry` 升序
3. 最终输出唯一排名 `1..N`

这条规则属于 v0.01 正式契约：

`排名必须唯一、稳定、可复现。`

---

## 5. 日级有效性契约

IRS 自 `2026-03-06` 起新增日级有效性约束：

1. 非交易日不得进入 `l2_industry_daily`
2. `industries_per_day < IRS_MIN_INDUSTRIES_PER_DAY` 时，当日 IRS 视为无效，不写入 `l3_irs_daily`
3. 缺基准指数时，当日评分仍可算，但必须在证据中标注

当前默认：

- `IRS_MIN_INDUSTRIES_PER_DAY = 25`

---

## 6. 当前已知现实问题

### 6.1 旧实现曾误用 111 桶

Week2 审计暴露出旧实现曾直接使用 `stock_basic.industry`，形成 `111` 个现实桶。

该问题已被纠正：

- 当前运行链路已切回申万一级优先
- `111` 桶不再是正式设计口径

### 6.2 raw 源库的申万成员仍不完整

虽然 raw 源库中存在：

- `raw_index_classify`
- `raw_index_member`

但短窗验证结果表明，当前 raw 申万成员源数据仍不完整。

当前真实状态是：

- 运行时目标口径：`31` 行业
- 短窗验证库现实结果：`27 + 未知`

因此，IRS 现在的主要阻塞不再是“行业桶定义错误”，而是：

`申万成员源数据仍需补采 / 清洗。`

### 6.3 过滤强度仍待校准

即使口径改回申万一级，IRS 仍需重新验证：

- `IRS_TOP_N=10` 是否过窄
- `+IRS` 是否会把机会压空

---

## 7. v0.01 正式方向

IRS 在 v0.01 的正式方向不是恢复旧版 6 因子全集，而是：

`先把两因子 IRS 做成现实可用、口径正确、可消融的行业过滤器。`

这意味着优先级必须是：

1. 行业口径正确
2. 数据覆盖可信
3. 排名契约稳定
4. 过滤强度合理

而不是一边口径没收口，一边继续加新因子。

---

## 8. 下一步

### 8.1 Data

优先刷新和清洗：

- `raw_index_classify`
- `raw_index_member`

目标是让执行库中的 `l1_sw_industry_member` 恢复到完整 `31` 行业覆盖。

### 8.2 Selector

在行业源数据补齐后，重跑：

- `l2_industry_daily`
- `l3_irs_daily`
- IRS 分布审计

### 8.3 过滤强度

重新比较：

- `Top 10`
- `Top 15`
- `Top 20`

并观察候选池、信号数和回测结果是否仍可交易。

---

## 9. 权威结论

当前 v0.01 的 IRS：

- 两因子框架成立
- 排名契约成立
- 正式行业口径已收回到 `SW2021 L1`

但还未完成：

1. 申万成员源数据收口
2. 过滤强度重新校准

所以 IRS 的下一步不是扩因子，而是：

`先把 SW31 数据链路做完整，再重新跑 +IRS 消融。`
