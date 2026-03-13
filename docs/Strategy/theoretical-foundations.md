# EmotionQuant 理论基础与方法论溯源

**版本**：`v1.2`  
**状态**：`Active`  
**封版日期**：`不适用（Active）`  
**变更规则**：`允许补充来源索引、采用边界与目录关系；不直接定义当前执行口径。`  
**上游文档**：`docs/Strategy/README.md`，`blueprint/README.md`

---

## 文档定位

本文档是 `docs/Strategy/` 的**总索引与边界说明**。

它只回答三件事：

1. `MSS / IRS / PAS` 的主要理论来源分别是什么。
2. 当前主线从这些来源中吸收了什么类型的方法论。
3. `Strategy/` 与 `blueprint/`、`docs/spec/` 的边界在哪里。

它不是执行 SoT，不负责定义当前参数、状态机、正式契约或实现计划。

---

## 当前主线口径

当前主线固定链路为：

`Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行`

与本目录相关的固定边界是：

1. `PAS` 负责个股形态层。
2. `IRS` 负责行业级后置排序增强。
3. `MSS` 负责市场级风险调节。
4. `Strategy/` 只提供来源、映射、背景和共享经验补充。

当前正式设计与执行口径，请查看 `blueprint/`。

---

## 1. MSS 理论来源

### 1.1 当前保留的核心参考

1. `MSS/market-sentiment-system-2024-analysis.md`
2. `MSS/manual-sentiment-tracking-experience.md`

### 1.2 主要提供的价值

`MSS` 方向当前主要从这些资料中吸收：

1. 市场广度、情绪强度、持续性的三维观测框架
2. 赚钱效应与亏钱效应的对称视角
3. 极端情绪样本与人工复核的经验背景
4. A 股涨跌停制度、T+1 语义对情绪系统的影响

### 1.3 不直接采用的内容

当前不直接继承：

1. 固定温度公式
2. 固定七阶段阈值
3. 固定仓位百分比表
4. 手工经验中的推测样例数值

---

## 2. IRS 理论来源

### 2.1 当前保留的核心参考

1. `IRS/shenwan-industry-classification.md`

### 2.2 主要提供的价值

`IRS` 方向当前主要从这些资料中吸收：

1. 正式行业口径应为 `SW2021 一级行业`
2. 个股与行业成员关系的维护边界
3. 行业指数和行业成员数据的更新与审计方式

### 2.3 不直接采用的内容

当前不直接继承：

1. 行业生命周期的静态 `PE / PB` 权重映射
2. 牛熊阶段行业配置表
3. 任意“某阶段超配某行业”的经验结论

---

## 3. PAS 理论来源

### 3.1 当前保留的核心参考

1. `PAS/lance-beggs-ytc-analysis.md`
2. `PAS/volman-ytc-mapping.md`
3. `PAS/xu-jiachong-naked-kline-analysis.md`
### 3.2 主要提供的价值

`PAS` 方向当前主要从这些资料中吸收：

1. `YTC` 五形态框架：`BOF / BPB / PB / TST / CPB`
2. 结构优先于单根 K 线的价格行为思想
3. `Volman -> YTC` 的微观结构映射线索
4. `BOF / Pin Bar` 的 A 股补充语境
5. A 股语境下的价格行为语言收口经验

### 3.3 不直接采用的内容

当前不直接继承：

1. 外汇盘中 `tick` 级触发细节
2. 原书中的固定成功率、盈亏比和精确交易管理
3. 战役专属 contrary alpha 推测
4. 历史阶段性实施计划与旧周计划

---

## 4. 目录边界

### 4.1 `Strategy/` 做什么

`Strategy/` 负责：

1. 来源梳理
2. 方法论映射
3. 采用边界说明
4. 共享经验补充

### 4.2 `Strategy/` 不做什么

`Strategy/` 不负责：

1. 当前主线正式设计
2. 当前实现方案
3. 当前执行拆解
4. 测试证据和 Gate 结论
5. 战役专属对象卡、contract note 与身份记录

### 4.3 正式入口

1. 当前设计 SoT：`blueprint/01-full-design/`
2. 当前实现方案：`blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
3. 当前执行拆解：`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
4. 当前治理状态：`docs/spec/common/records/development-status.md`

---

## 5. 使用建议

阅读顺序建议固定为：

1. 先看 `docs/Strategy/README.md`
2. 再按模块看 `MSS / IRS / PAS` 的共享来源文档
3. 需要落地实现时，立即回到 `blueprint/`
4. 需要证据和进度时，回到 `docs/spec/`

---

## 6. 相关文档

1. `docs/Strategy/README.md`
2. `docs/Strategy/MSS/README.md`
3. `docs/Strategy/IRS/README.md`
4. `docs/Strategy/PAS/README.md`
5. `docs/Strategy/MSS/market-sentiment-system-2024-analysis.md`
6. `docs/Strategy/IRS/shenwan-industry-classification.md`
7. `docs/Strategy/PAS/lance-beggs-ytc-analysis.md`
8. `docs/Strategy/PAS/volman-ytc-mapping.md`
9. `docs/Strategy/PAS/xu-jiachong-naked-kline-analysis.md`
10. `blueprint/README.md`
