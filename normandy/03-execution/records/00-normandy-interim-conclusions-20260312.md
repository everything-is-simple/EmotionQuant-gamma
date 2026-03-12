# Normandy Interim Conclusions

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `第二战场当前阶段性研究结论与后续研究清单`

---

## 1. 当前已经可以写死的结论

截至 `2026-03-12`，`Normandy` 当前已经可以固定下面这些结论：

1. `BOF` 是当前 `PAS raw alpha baseline`
2. `BOF` 接下来不再作为“待证对象”，而是作为所有候选的固定对照与尺子
3. `BPB` 当前 standalone detector 路线视为 `no-go`
4. `FB` 是当前唯一通过门槛的第二 alpha 候选，但仍带风险标记
5. `RB_FAKE` 当前更像 `BOF` 的 Volman 化窄子集，不像第二条独立 alpha 链
6. `SB` 当前不退场，但先进入 detector refinement 队列
7. `PB / TST / CPB` 暂不再以“谁接班 BOF”的方式继续平行竞争

---

## 2. 当前对象分层

| 对象 | 当前定位 | 当前处理 |
|---|---|---|
| `BOF` | 固定 baseline / control | 所有新候选的统一对照尺 |
| `FB` | `qualified_second_alpha_candidate_with_risk_flags` | 继续做稳定性与 purity 审核 |
| `SB` | 有理论吸引力但 detector 过宽 | 延后进入 refinement / no-go 判定 |
| `RB_FAKE` | `BOF` 的 Volman 化窄子集 | 进入观察池，不抢第二 alpha 主位 |
| `PB / TST / CPB` | 未通过 standalone provenance | 进入观察池，延后处理 |
| `BPB` | 当前 standalone `no-go` | 冻结当前 detector 路线 |

这里的 `BPB no-go` 只针对：

`当前 detector / 当前 standalone route`

它不等于：

`从 PAS taxonomy 中永久删除 BPB`

---

## 3. BOF 接下来该扮演什么角色

`BOF` 当前已经从“候选”变成“尺子”。

它接下来的职责固定为：

1. 所有新候选的固定 baseline
2. overlap / incremental / exit 对照基准
3. 执行语义变化时的健康检查对象

也就是说：

`BOF 接下来不再反复被拖回候选池，而是负责给所有新候选提供比较基准。`

---

## 4. 当前研究优先级

### 4.1 第一优先级：`N1.8 / Tachibana contrary alpha search`

研究内容：

1. 从 `Tachibana` 理论骨架抽出最小可执行 detector
2. 固定第一轮对象为 `TACHI_CROWD_FAILURE`
3. 与 `BOF_CONTROL` 做统一长窗 matrix
4. 判断这条线是独立 alpha、`BOF` 子集，还是当前 `no-go`

预计时间：

1. detector formalization：`1 ~ 2` 天
2. 长窗回放：`2 ~ 3` 小时
3. digest / record：`0.5 ~ 1` 天

合计：`2 ~ 3` 天

要求深度：

`足以回答“立花义正最核心的那条 crowd-failure 逻辑，能否形成可复现的 A 股日线 alpha”。`

### 4.2 第二优先级：`N1.7 / FB stability and purity`

研究内容：

1. `FB` 的 regime slicing
2. `FB` 的 first-pullback purity audit
3. `FB` 对 `BOF` 的补充性确认
4. `FB` 是否值得进入 `N2`

预计时间：

1. 文档与脚本骨架：`0.5` 天
2. 分析与证据：`1.0 ~ 1.5` 天
3. 结论 record：`0.5` 天

合计：`2 ~ 3` 天

要求深度：

`足以判断 FB 是继续深挖，还是先收缩 detector。`

### 4.3 第三优先级：`N1.9 / SB refinement or no-go`

研究内容：

1. 收窄 `SB detector`
2. 排查第二次失败语义是否被杂样污染
3. 判断 `SB` 是 detector 问题，还是对象本身在当前系统语义下不成立

预计时间：

1. detector 收缩与短窗复核：`1 ~ 2` 天
2. 长窗复核与结论：`1 ~ 2` 天

合计：`2 ~ 4` 天

要求深度：

`足以在 retain / delay / no-go 三者中做出正式裁决。`

### 4.4 第四优先级：`N2 / controlled exit decomposition`

前提：

`只在 FB 已经通过 N1.7 后才开。`

研究内容：

1. 先做 `BOF vs FB`
2. 判断 `FB` 是买对卖坏，还是 entry 本身仍不够稳
3. 暂不把全部 `PAS` 一起拖入 exit 拆解

预计时间：

`2 ~ 3` 天

要求深度：

`足以决定 FB 后续应继续修 entry，还是转向修 exit。`

---

## 5. Volman 延后研究清单

以下对象当前不跑正式长窗，但已经正式进入研究清单，后续不得遗忘：

1. `RB_TRUE`
   - 角色：真突破 continuation
   - 当前定位：晚于 `RB_FAKE / FB / SB` 的第二层候选
2. `IRB`
   - 角色：handle / boundary breakout timing refinement
   - 当前定位：更像 sidecar，不先独立 detector 化
3. `DD`
   - 角色：hold / test 的 micro trigger
   - 当前定位：更像 sidecar，不先独立 detector 化
4. `BB`
   - 角色：pressure / compression enhancer
   - 当前定位：质量层，不先独立 detector 化
5. `ARB`
   - 角色：复合型结构 bias
   - 当前定位：后期 composite research object

这一组对象当前统一归类为：

`Volman deferred queue`

---

## 6. Tachibana 研究清单

`立花义正` 当前也已经正式纳入后续研究清单。

但它的定位必须写死：

1. 它不是当前 `PAS` taxonomy 的新形态来源
2. 它不是当前 `MSS` 的直接替代方案
3. 它更像一套：
   - contrary doctrine
   - crowd-extreme observation framework
   - execution / risk rhythm discipline

当前更合理的后续研究入口是：

1. `TACHI_CROWD_FAILURE`
   - 当前定位：第一条最小可执行 entry 假设
2. `Tachibana contrary theory dossier`
   - 当前定位：理论骨架留档
3. `extreme sentiment sample study`
   - 当前定位：若第一轮 entry 成立，再深挖样本族
4. `休息 / 撤退 / 试探仓位` 的执行纪律研究
   - 当前定位：第二层，不进入首轮 entry detector

这条线当前统一归类为：

`Outside-PAS but Normandy-relevant research queue`

---

## 7. 当前不该做的事

当前阶段明确不建议：

1. 再把 `PB / TST / CPB / SB / FB` 一起拖进新一轮大混战
2. 继续围绕 `BPB` 烧时间
3. 在 `FB` 还没通过稳定性审查前，直接讨论主线升格
4. 把 `Tachibana` 粗暴翻译成“把 PAS 反着做”

---

## 8. 当前一句话路线图

`BOF 作为尺子固定，Tachibana 的 TACHI_CROWD_FAILURE 先接受首轮 alpha 审核，FB 暂居第二优先级继续深挖，SB 进入延后 refinement，剩余 Volman 结构与 Tachibana 第二层议题统一进入 backlog。`
