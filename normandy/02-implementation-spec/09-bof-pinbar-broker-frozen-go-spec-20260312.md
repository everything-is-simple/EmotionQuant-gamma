# BOF / Pinbar Broker-Frozen Go Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `Normandy / PAS-only broker-frozen go path`

---

## 1. 定位

本文不是新的主线实现方案。

本文只定义 `Normandy` 当前为了顺利走到 `go / no-go` 所必须补上的那条受控路径：

`在无 MSS / 无 IRS 硬过滤的前提下，保持同一套 Broker 出场语义不变，回到 BOF family 内部做 key-level / pinbar quality split，并决定是否有分支值得进入 N2。`

---

## 2. 为什么现在必须补这张 spec

截至 `2026-03-12`，下面这些事实已经同时成立：

1. `BOF` 已被正式固定为 `PAS raw alpha baseline / control`
2. `FB / SB / Tachibana` 目前都没有形成 `N2-ready` 的明确新主位
3. 来源资料回看后，`BOF / pinbar / key-level` 仍然是三套资料共同指向的最大交集
4. 代码层的 `Normandy` backtest 已经在复用同一套 Broker 内核，但文档层尚未把这个问题正式冻结成一条 `broker-frozen gate`

因此现在最缺的不是再开一条更远的新 family，而是把这条路径写死：

`先在同一套 Broker 下判断 entry 本身有没有更纯的 alpha。`

---

## 3. 当前只回答什么问题

本文当前固定只回答一个问题：

`在 A 股日线 + T+1 Open + 当前统一 Broker exit semantics + 无 MSS / 无 IRS 的条件下，BOF family 内部是否存在一个比 BOF_CONTROL 更值得继续推进的 quality branch。`

本文当前不回答：

1. `Tachibana` 整体是否值得继续扩张
2. `FB_BOUNDARY` 是否重新回到主队列
3. `pyramiding / split exits` 是否进入正式执行

---

## 4. 固定实验边界

当前实验固定允许：

1. 关闭 `MSS gate`
2. 关闭 `IRS` 前置硬过滤与排序增强
3. 保持当前统一 `Broker` 内核
4. 保持当前 `stop_loss + trailing_stop + T+1 Open` 出场语义
5. 在 `BOF` family 内做受控 quality split

当前实验固定不允许：

1. 新开 standalone `Pinbar` detector family
2. 把 `金字塔加仓` 并入首轮 provenance
3. 一边做 entry split，一边顺手改 exit 规则
4. 把 `Tachibana / FB / SB` 拉回同一张主比较表

---

## 5. 固定比较对象

当前比较对象固定为四支：

1. `BOF_CONTROL`
   - 当前正式 baseline
2. `BOF_KEYLEVEL_STRICT`
   - 只保留关键位更强、失败位置更清楚的 `BOF` 子集
3. `BOF_PINBAR_EXPRESSION`
   - 只保留出现更明显 `pinbar / 合成 pinbar` rejection 表达的 `BOF` 子集
4. `BOF_KEYLEVEL_PINBAR`
   - 同时满足关键位更强和 pinbar 表达更清楚的交集子集

这里必须明确：

`这四支不是四个新 taxonomy，而是 BOF family 的 quality branches。`

---

## 6. 固定执行拆解

### 6.1 `N1.11 / BOF pinbar quality provenance`

职责：

1. 在同一窗口、同一 Broker 下重放四支分支
2. 读出 `trade_count / EV / PF / MDD / participation`
3. 判断是否存在 retained branch

### 6.2 `N1.12 / BOF family stability or no-go`

职责：

1. 仅对 `N1.11` 的 retained branch 做稳定性与 purity 审核
2. 复核跨年、环境桶、selected/executed gap 与 overlap / incremental
3. 决定它是否有资格进入 `N2`

---

## 7. 固定证据要求

本路线固定要求四类证据：

1. `bof_quality_matrix`
2. `bof_quality_digest`
3. `selected_trace / overlap / incremental diagnostics`
4. `bof_quality_stability_report`

---

## 8. Go / No-Go 规则

只有在以下条件同时成立时，才允许把 retained branch 判为 `go-to-n2`：

1. 相对 `BOF_CONTROL` 仍保持正向或更优的 `EV`
2. 样本量与参与率不低于当前 Normandy 继承门槛
3. 没有出现明显的跨年崩塌或主环境负读数吞没
4. 没有出现“selected 很多，但 executed 极少”的严重脱节

否则统一裁定为：

`branch no-go, keep BOF_CONTROL as sole baseline`

---

## 9. 当前一句话方案

`先别继续找更远的新 family；先在无 MSS / 无 IRS、同一套 Broker 出场语义下，把 BOF / key-level / pinbar 这条线读到可以正式 go / no-go 为止。`
