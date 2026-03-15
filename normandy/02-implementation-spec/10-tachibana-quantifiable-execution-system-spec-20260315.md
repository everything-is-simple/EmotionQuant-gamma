# Tachibana Quantifiable Execution System Spec

**文档版本**：`v0.01`  
**文档状态**：`Active`  
**日期**：`2026-03-15`  
**适用范围**：`Normandy / 立花义正方法再梳理与可验证化`  
**上游材料**：
- `G:\《股市浮沉二十载》\2012.(Japan)【立花义正】\你也能成为股票操作高手（立花义正）.pdf`
- `G:\《股市浮沉二十载》\2012.(Japan)【立花义正】\你也能够成为股票高手：一位从零开始学炒股的职业炒家的不平凡操作记录(高清).pdf`
- `G:\《股市浮沉二十载》\2012.(Japan)【立花义正】\你也能成为股票操作高手（立花义正）PDF转图片版`
- `G:\《股市浮沉二十载》\2012.(Japan)【立花义正】\丽花义正-交易谱（1975.01-1976.12）`
- `normandy/01-full-design/90-research-assets/tachibana-yoshimasa-analysis.md`
- `normandy/02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md`

---

## 1. 这次为什么重写

`05-tachibana-contrary-alpha-search-spec-20260312.md` 抓到了一条有价值的最小假设：

`先有 crowd extreme，再有 crowd failure reclaim。`

但它仍然只抓到了立花方法的一小段 `entry alpha`，没有抓住原书最珍贵的部分：

1. `试单 -> 母单 -> 加减 -> 撤退 -> 休息` 的执行状态机
2. `未平仓路径` 比单次买点更重要
3. 仓位是被市场验证出来的，不是一次性决定出来的
4. 立花真正关心的不是“猜这次会不会涨”，而是“给自己一点风险空间，去博一个值得博的机会”

因此本次重写的目标不是把立花改写成另一个 `PAS detector`，而是把它整理成一套：

`可量化、可回放、可验证，但不伪装成已完全 formalize 的执行系统。`

---

## 2. 当前固定判断

本次重写后，`Normandy` 对立花方法固定保留下面七条判断：

1. 它首先是一套 `执行 doctrine`，其次才是一套 `机会识别 doctrine`。
2. 它不能被压缩成“逢极端就反向”的一句话。
3. 它最核心的动作不是重仓开火，而是 `试单`。
4. `母单` 不是仓位大小描述，而是“试探成功后被确认保留的主仓”。
5. 它更接近 `离散档位调仓`，而不是连续函数型优化仓位。
6. 它最珍贵的验证对象不是最终收益，而是 `部位如何一路演化`。
7. 在 A 股语义下，它最值得研究的不是“完全复刻”，而是“哪些机制可以迁移，哪些机制不可迁移”。

---

## 3. 原书中最值得 formalize 的五个对象

结合台湾版书页与交易谱材料，当前最稳定的五个对象如下。

### 3.1 `test_order`

证据来源：

1. 书页 `B0161` 明确写出 `使用测试单`
2. 同页同时写出 `失败就平掉`
3. 同页同时写出 `成功时把测试单转成母单`

formal 语义：

1. `test_order` 是低承诺、低暴露、允许快速失败的先手仓位
2. 它的目标不是赚钱，而是向市场购买确认权
3. 它不能和普通“首次建仓”混为一谈

### 3.2 `mother_position`

证据来源：

1. 书页 `B0161` 的 `测试单转成母单`
2. 书页 `B0162` 的连续例子里，仓位不是一次性满仓，而是被确认后逐步扩大

formal 语义：

1. `mother_position` 是经过初始验证后被保留的主仓
2. 后续加码不是围绕“零仓”展开，而是围绕 `mother_position` 展开
3. 这意味着系统必须认识 `position identity`，不能只认识独立订单

### 3.3 `discrete_ladder`

证据来源：

1. 书页 `B0176-B0177` 展现了类似 `2 -> 5 -> 10 -> 15 -> 20` 的离散部位变化
2. 相邻调整之间常见 `2-5` 天间隔，但并非严格固定

formal 语义：

1. 仓位变化是离散档位，而不是平滑连续曲线
2. 档位变化既受价格反馈影响，也受时间节奏影响
3. “多少档”与“多久一调”都应作为独立研究对象

### 3.4 `retreat_and_rest`

证据来源：

1. 书中反复强调错了就退，不硬扛
2. 多处强调休息、停手与等待下一次机会

formal 语义：

1. 立花方法不是只研究怎么进，还研究何时停止继续试错
2. `休息` 不是情绪词，而是可研究的账户状态
3. 一个完整系统至少要有 `active / retreat / rest` 三种大状态

### 3.5 `path_over_outcome`

证据来源：

1. 交易谱最珍贵的不是“这一年赚了多少”
2. 而是每天的价位表与部位变化让我们有机会回看 `未平仓路径`

formal 语义：

1. 核心验证对象不是单笔胜率，不是单次 entry quality
2. 而是 `从 test_order 到 final_exit 的路径是否忠实`
3. 如果只能验证最终收益，不能验证路径，就不能说“验证了立花方法”

---

## 4. 立花系统的最小可量化架构

本 spec 当前把立花方法拆成五层，不再把它压成单一 detector。

### 4.1 `L1 Opportunity Context`

职责：

1. 识别 `crowd extreme / crowd failure / contrary opportunity`
2. 它只回答：现在是否值得发出 `test_order`

当前可复用对象：

1. `TACHI_CROWD_FAILURE`
2. 其他后续可能的 `contrary context detector`

注意：

1. 这一层不是立花系统全体
2. 它只是“是否值得试单”的机会过滤层

### 4.2 `L2 Probe Decision`

职责：

1. 定义 `什么时候发试单`
2. 定义 `试单最大风险预算`
3. 定义 `试单失败何时归零`

当前最小 formal 对象：

1. `probe_trigger`
2. `probe_unit`
3. `probe_invalidated`
4. `probe_timeout`

### 4.3 `L3 Mother Position Confirmation`

职责：

1. 判断试单是否从 `probe` 升格为 `mother_position`
2. 定义升格后的最小保留仓
3. 定义不能升格时是否应归零

当前最小 formal 对象：

1. `promotion_trigger`
2. `mother_unit`
3. `promotion_window`

### 4.4 `L4 Discrete Ladder Management`

职责：

1. 定义后续加码、减码、锁盈、缩量
2. 用离散档位描述部位变化
3. 同时记录调整间隔与原因

当前最小 formal 对象：

1. `ladder_state`
2. `ladder_step`
3. `days_since_last_step`
4. `scale_reason`
5. `descale_reason`

### 4.5 `L5 Retreat / Rest`

职责：

1. 定义什么时候退出本轮博弈
2. 定义什么时候进入休息期
3. 定义什么时候可以重新开始下一轮试探

当前最小 formal 对象：

1. `retreat_trigger`
2. `rest_days`
3. `rearm_condition`

---

## 5. 什么是“可量化”的，什么暂时不是

下表给出当前边界。

| 原书语义 | 当前是否可量化 | 当前 formal 对象 | 当前证据来源 |
|---|---|---|---|
| 测试单 | 可量化 | `probe_unit / probe_trigger / probe_invalidated` | `B0161` |
| 母单 | 可量化 | `mother_unit / promotion_trigger` | `B0161-B0162` |
| 分几次加减 | 可量化 | `ladder_state / ladder_step` | `B0176-B0177` |
| 调整间隔 | 可量化 | `days_since_last_step` | `B0176-B0177` |
| 错了就退 | 可量化 | `retreat_trigger / full_flatten` | 全书反复出现 |
| 休息 | 半可量化 | `rest_days / rearm_condition` | 书中纪律语义 |
| 市场节奏感 | 暂不可完全量化 | 先保留为人工标签 | 交易者经验层 |
| 人的胆量与克制 | 不量化 | 不进入第一轮 formal contract | 行为层 |
| 盘中读盘细节 | 当前不量化 | 明确排除 | 原书主观层 |

本 spec 的立场是：

`先 formalize 能稳定复核的对象，暂不伪装形式化那些本质上还停留在经验层的部分。`

---

## 6. 第一轮最小数据契约

如果要验证立花方法，必须先有比普通回测更细的对象。当前至少需要三张表。

### 6.1 `tachibana_market_bar`

字段建议：

1. `date`
2. `symbol`
3. `open`
4. `high`
5. `low`
6. `close`
7. `volume`
8. `calendar_index`

作用：

1. 提供价格背景
2. 为机会识别与路径回放提供标准时钟

### 6.2 `tachibana_position_ledger`

字段建议：

1. `date`
2. `symbol`
3. `action`
4. `units_delta`
5. `open_units`
6. `execution_price`
7. `cash_after`
8. `state_before`
9. `state_after`
10. `reason_tag`
11. `source`

说明：

1. `action` 至少包括 `probe_buy / add / reduce / flatten / idle`
2. `source` 必须区分 `book_manual_extract / xlsx_manual / replay_generated`

### 6.3 `tachibana_state_trace`

字段建议：

1. `date`
2. `symbol`
3. `context_state`
4. `execution_state`
5. `ladder_state`
6. `days_in_trade`
7. `days_since_last_step`
8. `rest_state`
9. `confidence_tag`
10. `annotation`

作用：

1. 把“为何今天没有动作”也纳入回放
2. 避免只记录成交，不记录状态变化

---

## 7. 第一轮验证标准

立花方法第一轮不能只看收益，必须同时看下面五类一致性。

### 7.1 `path fidelity`

问题：

1. 系统生成的仓位路径是否与原始交易谱接近
2. 接近的对象不是 exact price，而是 `加减节律` 与 `部位形状`

### 7.2 `state fidelity`

问题：

1. `probe -> mother -> ladder -> flatten -> rest` 的转换是否讲得通
2. 是否出现大量“理论上不该存在”的跳变

### 7.3 `capital discipline fidelity`

问题：

1. 单轮暴露是否始终受控
2. 是否存在与原书精神相反的“信念型加仓”

### 7.4 `timing fidelity`

问题：

1. 调整动作是否具有离散节律
2. 是否需要最小间隔、冷却期或观察期

### 7.5 `transplantability`

问题：

1. 迁移到 A 股 `T+1 Open` 语义后，哪些机制仍有效
2. 哪些机制因为制度差异直接失真

---

## 8. 正式验证路线

本研究不再一步跳到“A 股大样本 alpha”，而是按下面五条路线推进。

### 8.1 `Track T0: Ledger Reconstruction`

目标：

1. 先把 `丽花义正-交易谱（1975.01-1976.12）` 整理成结构化部位账
2. 这一步是全项目的根

最低交付：

1. `tachibana_tradebook_contract_note`
2. `tachibana_tradebook_extraction_matrix`
3. `tachibana_tradebook_reconstruction_digest`

### 8.2 `Track T1: Detector-Only Baseline`

目标：

1. 保留旧 `TACHI_CROWD_FAILURE` 作为机会层 baseline
2. 但明确它只服务 `L1 Opportunity Context`

最低交付：

1. `tachibana_context_detector_matrix`
2. `tachibana_context_detector_overlap_with_bof`

### 8.3 `Track T2: Probe-Mother Replay`

目标：

1. 在 `Pioneer` 单一标的上，先验证 `test_order -> mother_position`
2. 这一步只研究最小升格逻辑，不急于研究全套档位

最低交付：

1. `tachibana_probe_promotion_matrix`
2. `tachibana_probe_promotion_digest`

### 8.4 `Track T3: Discrete Ladder Replay`

目标：

1. 在原始交易谱上重放离散档位变化
2. 核心不是最优参数，而是“立花是不是确实在使用离散档位”

最低交付：

1. `tachibana_ladder_family_matrix`
2. `tachibana_ladder_family_digest`
3. `tachibana_path_similarity_record`

### 8.5 `Track T4: A-share Transplant`

目标：

1. 把 `probe / mother / ladder / rest` 迁移到 A 股 `T+1 Open`
2. 评估哪些对象仍可运行

最低交付：

1. `tachibana_a_share_boundary_note`
2. `tachibana_t1_open_execution_matrix`

### 8.6 `Track T5: BOF Entry + Tachibana Execution`

目标：

1. 检查 `BOF` 是否更适合作为机会发现器
2. 同时由立花 doctrine 管理仓位与退出节奏

这条线的真正问题不是：

`BOF 和立花谁更强`

而是：

`BOF 是否负责发现机会，立花是否负责管理这次机会。`

---

## 9. 明确的 no-go 边界

第一轮研究明确禁止下面五种偷懒做法。

1. 禁止把立花重新压回单一 detector。
2. 禁止用一组通用指标随意替代原书语义后，直接宣称“已量化立花”。
3. 禁止只看收益，不看 `未平仓路径`。
4. 禁止在未完成 `交易谱重建` 前，就报告“大样本已经验证成功”。
5. 禁止把原书中的主观盘中语义伪装成已经 formalize 的日线规则。

---

## 10. 与旧 spec 的关系

`05-tachibana-contrary-alpha-search-spec-20260312.md` 现在仍保留，但定位收缩为：

`立花系统的 L1 Opportunity Context 子规格。`

它不再代表立花方法整体，只代表：

1. 一条可研究的 contrary 机会检测器
2. 立花系统里“是否值得试单”的上游过滤器

因此后续口径应统一为：

1. `TACHI_CROWD_FAILURE != Tachibana`
2. `TACHI_CROWD_FAILURE ⊂ Tachibana execution system`

---

## 11. 当前最值得先做的两件事

### 11.1 先把交易谱做成“部位真相表”

这是当前最重要的工作。没有它，后面所有“量化立花”都容易退化成想象。

最低字段建议：

1. `date`
2. `close`
3. `buy_units`
4. `sell_units`
5. `open_units`
6. `avg_cost`
7. `state_tag`
8. `note`

### 11.2 把研究对象从“最优参数”改成“最忠实路径”

第一轮最应该问的是：

1. 系统能不能复现 `试单 -> 母单 -> 档位变化 -> 撤退 -> 休息`
2. 而不是“Sharpe 能不能再高一点”

---

## 12. 当前一句话定位

`立花义正在 Normandy 中不应再被理解为一条 contrary alpha detector，而应被重建为一套以 test_order、mother_position、discrete_ladder、retreat 与 rest 为核心对象的可验证执行系统。`
