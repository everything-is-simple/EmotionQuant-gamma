# EmotionQuant 仓库三线地图

**状态**: `Active`  
**日期**: `2026-03-16`  
**对象**: `仓库级历史线 / 主线 / 研究线拓扑说明`

---

## 1. 目标

本文只做一件事：

`把 EmotionQuant 仓库里“历史线 / 主线 / 研究线”三条线的边界写死。`

它不是新的系统设计正文，也不是新的 phase card。

它只负责回答：

1. 哪些目录属于历史线
2. 哪些目录属于当前主线
3. 哪些目录属于研究线
4. 哪些目录只负责治理、状态和参考

---

## 2. 三条线

### 2.1 历史线

历史线固定为：

1. `docs/design-v2/`
2. `docs/spec/v0.01/`

它只承载：

1. `v0.01 Frozen` 历史基线
2. 历史执行计划与历史治理痕迹
3. 回退参考与回归对照

它不再承载：

1. 当前主线设计正文
2. 当前主线实现方案
3. 当前研究线实验方案

### 2.2 主线

主线固定为：

1. `blueprint/`
2. `docs/spec/v0.01-plus/`

其中：

1. `blueprint/` 负责当前主开发线的设计正文、实现方案与执行拆解
2. `docs/spec/v0.01-plus/` 负责当前主线的治理归档、evidence 与 records

当前主线名称固定为：

`v0.01-plus`

### 2.3 研究线

研究线当前固定为：

1. `normandy/`
2. `positioning/`
3. `gene/`

它们的角色固定为：

1. `normandy/`
   - 独立研究战场
   - 用于证明 `raw alpha provenance`
   - 用于拆解 `exit damage / execution damage`
2. `positioning/`
   - 独立仓位研究战场
   - 用于在固定 `no IRS / no MSS` baseline 下验证 `买多少 / 卖多少`
   - 先做 `position sizing`，后做 `partial-exit / scale-out`
3. `gene/`
   - 独立历史波段标尺研究战场
   - 用于定义 `趋势 / 波段 / 转折 / 新高新低`
   - 用于回答 `当前这段走势在其自历史里算什么级别`
4. 三条研究线都不直接改写当前主线 SoT

当前必须明确写死：

1. `Normandy` 不是 `v0.01` 的子版本号，也不是新的版本线。
2. `Positioning` 不是 `v0.01` 的子版本号，也不是新的版本线。
3. `Gene` 不是 `v0.01` 的子版本号，也不是新的版本线。

它们都是研究线，不是版本线。

---

## 3. 其他目录的角色

### 3.1 跨线治理账本

下面这些目录不属于三条线中的任何一条“设计正文线”，它们是治理账本层：

1. `docs/spec/common/records/`
2. `docs/spec/common/README.md`

它们负责：

1. 当前状态
2. 技术债
3. 可复用资产
4. 仓库拓扑说明

它们不负责现行设计正文。

### 3.2 来源与参考层

下面这些目录属于来源、观察与参考层：

1. `docs/Strategy/`
2. `docs/reference/`
3. `docs/observatory/`
4. `docs/workflow/`

它们负责：

1. 方法论来源
2. 外部规则与运维参考
3. 观察、复盘与审查
4. 固定工作流

它们不直接定义当前主线 SoT。

---

## 4. 升格规则

三条线之间的关系固定为：

1. 历史线不可被研究线反写
2. 研究线不可直接宣布主线改写
3. 主线若要吸收研究线结论，必须先经过正式 record
4. 升格后的结论必须迁回 `blueprint/` 与对应的 `docs/spec/v0.01-plus/`

换句话说：

1. `Normandy` 可以找到答案
2. `Positioning` 可以找到控制层答案
3. `Gene` 可以给出历史波段标尺
4. 但三者都不能靠自身目录结构直接变成新主线

---

## 5. 当前仓库一句话口径

`docs/design-v2/` 是历史线，`blueprint/` 是主线，`normandy/`、`positioning/` 与 `gene/` 是研究线，`docs/spec/common/records/` 是跨线状态账本。`
