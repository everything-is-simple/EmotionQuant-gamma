# Volman Second Alpha Search Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `第二战场第二条 alpha 搜索支线`

---

## 1. 定位

本文不是对 `N1 / PAS 五单形态 + YTC5_ANY` 结论的推翻。

本文只定义一条有边界的扩展搜索线：

`在 BOF 已被重新钉实为当前 baseline 之后，继续寻找“第二个自带 alpha 的人”。`

这里的“第二个”，不是要抹掉 `BOF` 的长子地位，而是要回答：

`除了当前已验证的 BOF 之外，还有没有另一类 entry object 值得被单独证明。`

---

## 2. 为什么要单开这条线

截至 `2026-03-12`，第二战场已经有两个固定结论：

1. `N1` 首轮矩阵在 `BOF / BPB / PB / TST / CPB / YTC5_ANY` 内，没有找到能推翻 `BOF` 的非 `BOF` shape
2. `BOF` 已经被来源文档、工程实现和三年长窗证据重新固定为当前系统的 baseline

这意味着下一步不能继续做两件事：

1. 不能假装 `PB / TST / CPB / BPB` 中已经有人接班
2. 也不能因为首轮没找到，就直接宣布“第二个 alpha 不存在”

因此必须扩展候选池，但扩展必须有边界。

---

## 3. 当前唯一扩展方案

当前允许的扩展搜索线固定为：

`Volman PAS v0 候选 provenance`

首轮只允许保留三类独立候选：

1. `RB_FAKE`
2. `SB`
3. `FB`

并固定保留一个控制组：

4. `BOF_CONTROL`

这里的语义固定为：

1. `BOF_CONTROL` = 当前系统已验证 baseline，对照组
2. `RB_FAKE` = Volman 语义下的假突破失败对象
3. `SB` = 第二次失败后的再突破对象
4. `FB` = 首次回撤恢复对象

---

## 4. 为什么这批候选只保留这三类

因为当前只允许先回答：

`谁最像 standalone alpha object。`

在这条标准下：

1. `RB_FAKE / SB / FB` 有完整结构语义
2. 它们都能独立定义触发与失效
3. 它们都不只是别的形态的 quality 加分项

而下面这些暂不单独升格：

1. `IRB`
2. `DD`
3. `BB`
4. `ARB`

原因是它们在当前阶段更像：

1. `timing refinement`
2. `micro trigger`
3. `pressure / quality enhancer`
4. `composite bias layer`

---

## 5. SB 的特殊约束

当前必须把一条边界写死：

`SB 不得因为实现复杂、结构跨度更长或更像 CPB/TST 扩展版，就被从第一批候选里删除。`

原因不是主观偏好，而是结构逻辑本身成立：

1. 第一次失败制造怀疑
2. 第二次失败制造恐慌
3. 这类 `double failure liquidation` 理论上可能形成不同于 `BOF` 的第二条 alpha 链

因此当前对 `SB` 的正式态度固定为：

1. 不能先宣布它更强
2. 但也不能因为复杂就把它排除出首批搜索对象

---

## 6. 当前实验允许做什么

当前实验固定允许：

1. 定义 `RB_FAKE / SB / FB` 的最小 detector 语义
2. 在统一长窗口上比较 `BOF_CONTROL / RB_FAKE / SB / FB`
3. 输出各候选的 `trade_count / EV / PF / MDD / participation`
4. 输出与 `BOF_CONTROL` 的 overlap / incremental attribution
5. 明确谁最像“第二个自带 alpha 的人”

当前实验固定不允许：

1. 直接切换当前主线默认路径
2. 把 `IRB / DD / BB / ARB` 提前升格为第一批 standalone detector
3. 在这条线上重新打开 `MSS / Broker` 微调
4. 把 `IRS` 拉回前置硬过滤
5. 因为某一段短窗结果漂亮，就宣布新候选接班 `BOF`

---

## 7. 证据要求

这条搜索线至少要产出下面四类证据：

1. `volman candidate matrix summary`
2. `BOF overlap / incremental trade decomposition`
3. `candidate digest`
4. `record / gate-style narrative`

如果某个候选要被带去后续更深阶段，至少要同时回答：

1. 它是替代型 alpha，还是互补型 alpha
2. 它的 edge 主要来自 entry 本身，还是只是更好的 timing

---

## 8. 出场条件

这条扩展线只有在以下条件之一成立时才允许出场：

1. 找到至少一个非 `BOF` 候选，证明其具备独立 raw alpha 价值
2. 或者明确证明 `RB_FAKE / SB / FB` 在当前系统语义下都不构成第二个 alpha 候选

无论哪种结果，都必须留下正式 record。

---

## 9. 当前一句话方案

`保持 BOF 为固定 baseline，对 Volman 三候选 RB_FAKE / SB / FB 做一轮受控 provenance 搜索，专门回答“第二个自带 alpha 的人是谁”。`
