# IRS 算法设计

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变 v0.01 Frozen 历史基线的前提下，对当前主线中的 IRS 角色、算法细案与证据回写做受控修订。`  
**上游文档**: `docs/spec/v0.01-plus/README.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`  
**创建日期**: `2026-03-06`  
**最后更新**: `2026-03-08`  
**对应模块**: `src/selector/irs.py`, `src/strategy/ranker.py`, `src/data/cleaner.py`  
**理论来源**: `docs/Strategy/IRS/`

---

## 1. 当前主线定位

在 `v0.01-plus` 当前主线中，IRS 的职责是：

`给 BOF 触发后的候选信号提供行业横截面增强。`

它当前不再承担：

- Selector 前置硬过滤
- 候选池行业拦截
- 市场级停手判断

当前主线消费者已经切换为：

`Strategy / Ranker`

---

## 2. 理论基础

IRS 的理论基础仍来自申万行业分类体系和行业轮动实践：

1. `docs/Strategy/IRS/shenwan-industry-classification.md`

核心设计原则不变：
- 行业分类标准化（申万一级为唯一事实源）
- 相对强度优先（行业 vs 基准）
- 资金流向验证（量价配合）
- 不依赖宏观叙事（纯数据驱动）

变化只在系统职责：
- 过去：Selector 前置过滤器
- 现在：Strategy 后置排序因子

---

## 3. 正式行业口径

当前正式行业口径固定为：

`SW2021 一级 31 行业`

运行时优先级：

1. `l1_sw_industry_member`
2. 无匹配时记为 `未知`

说明：
- `未知` 可以留在候选池中
- 但当前主线中，`未知` 行业应按 fallback 进入 `IRS=50` 中性处理
- 不允许因为行业缺失直接把 BOF 候选挡在主线之外

---

## 4. 输入与数据边界

IRS 当前读取：

- `l2_industry_daily`
- `l1_index_daily`

`l2_industry_daily` 的正式生成方式为：

- 先按 `l1_sw_industry_member` 确定个股所属申万一级行业
- 无 SW 匹配时归入 `未知`
- 再把个股日线聚合到行业日线
- 非交易日不进入 `L2/L3`

---

## 5. 当前算法定义

### 5.1 两因子框架

当前实现仍保留两因子：

1. **RS（相对强度，55%）**
   - `industry_pct_chg - benchmark_pct_chg`
2. **CF（资金流向，45%）**
   - `flow_share + amount_delta_10d`

综合得分：

```text
total_score = 0.55 * rs_score + 0.45 * cf_score
```

### 5.2 当前主线消费方式

当前主线不再把 `IRS` 用作前置 `Top-N` 行业过滤。

当前主线使用方式是：

1. `IRS` 在行业层产出 `score / rank`
2. `Strategy / Ranker` 在个股 `BOF` 触发后，为信号附加 `irs_score`
3. `irs_score` 用于形成 `final_score`

因此，IRS 当前职责应解释为：

`行业横截面增强因子`

而不是：

`Selector 行业门控器`

---

## 6. 日级有效性契约

IRS 当前仍遵循：

1. 非交易日不得进入 `l2_industry_daily`
2. `industries_per_day < IRS_MIN_INDUSTRIES_PER_DAY` 时，当日 IRS 视为无效，不写入 `l3_irs_daily`
3. 缺基准指数时，当日评分仍可算，但必须在证据中标注
4. 主线消费时若 `IRS` 缺失，则按 `50` 中性分 fallback，并保留可追溯标记

---

## 7. 当前已知现实问题

### 7.1 旧前置过滤口径已经过时

过去 IRS 的问题是：

- `Top-N` 过滤会在 BOF 之前误杀样本
- 很难解释收益变化到底来自行业拦截还是来自排序增强
- 容易把 Selector 和 Strategy 的边界写混

因此在当前主线中，`IRS hard filter` 已降级为历史对照逻辑。

### 7.2 当前核心问题转成“排序是否稳定有效”

现在真正要验证的是：

- `IRS` 是否稳定改善排序质量
- `IRS` 在不同 `Top-N / max_positions` 约束下是否真的提高执行结果
- `IRS` 的收益改善是否具有更长窗口稳定性

---

## 8. 版本演进路径

### 8.1 v0.01 Frozen（历史）

- IRS 作为 Top-N 行业过滤器
- 保留为历史对照与回退参考

### 8.2 v0.01-plus（当前主线）

- IRS 改为后置排序因子
- 不再前置过滤
- 当前重点是验证排序增益是否稳定存在

### 8.3 后续版本

若后续证据支持，IRS 可继续扩展：
- 进一步细化 score 映射
- 结合更多行业内结构因子
- 研究不同市场环境下的权重调整

但这些都应建立在当前主线证据稳定之后。

---

## 9. 权威结论

当前主线里的 IRS：

- 行业口径已经收回到 `SW2021 一级 31 行业`
- 算法框架仍是 `RS + CF`
- 执行职责已经从“前置过滤”切换到“后置排序增强”
- 下一步重点不是继续扩因子，而是继续验证其排序收益是否稳定成立

---

## 10. 参考文献

1. `docs/Strategy/IRS/shenwan-industry-classification.md`
2. `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
3. `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`
