# 核心算法设计（算法级 SoT）

**版本**: `v0.01-v0.06 设计入口`  
**状态**: `Frozen`（算法级 SoT 入口）  
**封版日期**: `2026-03-07`  
**变更规则**: `算法语义变更必须同时具备设计修订与证据支撑；若触及系统执行语义，以上游 baseline 为准。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

## 定位

`docs/design-v2/03-algorithms/core-algorithms/` 存放 MSS / IRS / PAS 的当前算法级设计，以及跨版本集成模式说明。

这里回答的是“当前算法怎么算”，不是“理论来源在哪里”或“证据放在哪里”。跨模块执行语义以 `docs/design-v2/01-system/system-baseline.md` 为准；当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准；阶段证据与版本验收统一归档到 `docs/spec/`。

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 系统基线 | `docs/design-v2/01-system/system-baseline.md` | 确认跨模块执行语义与总边界 |
| MSS 算法 | `mss-algorithm.md` | 查看市场情绪算法定义 |
| IRS 算法 | `irs-algorithm.md` | 查看行业轮动算法定义 |
| PAS 算法 | `pas-algorithm.md` | 查看价格行为算法定义 |
| 集成模式 | `down-to-top-integration.md` | 查看 v0.01 与 v0.02+ 的集成演进 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 查看当前治理阶段与重启条件 |

## 结构

```text
core-algorithms/
├── README.md                    # 本文件
├── mss-algorithm.md             # MSS 当前算法口径
├── irs-algorithm.md             # IRS 当前算法口径
├── pas-algorithm.md             # PAS 当前算法口径
└── down-to-top-integration.md   # 集成模式与演进边界
```

## 使用规则

1. 本目录是算法级 SoT；若与模块设计、理论研究或评审附录冲突，先回到 `docs/design-v2/01-system/system-baseline.md` 判断总边界。
2. 理论来源与采用理由放在 `docs/Strategy/`，不在本目录重复展开研究材料。
3. 版本证据、回测结果、消融实验与验收结论，统一进入 `docs/spec/<version>/evidence/` 或对应 records。
4. 当前是否继续推进 `v0.01` 实现，不在本目录维护，统一查看 `docs/spec/common/records/development-status.md`。
5. 算法语义变更必须同时具备设计修订与证据支撑，不接受只改 README 或只改代码。

## 当前版本范围

| 版本 | MSS | IRS | PAS | 集成模式 |
|---|---|---|---|---|
| v0.01 | 三态硬门控 | Top-N 硬过滤 | BOF 单形态闭环 | Top-Down |
| v0.02 | 软评分模式 | 软评分 + 龙头 | BOF + BPB | Down-to-Top |
| v0.03 | 七阶段周期 | 牛股基因聚合 | TST / PB | 软评分 |
| v0.04 | 趋势方向 | 行业生命周期 | CPB + 失败处理 | 软评分 |
| v0.05 | 动态仓位 | 政策事件 | 形态强度评分 | 软评分 |
| v0.06 | 自适应阈值 | 自适应权重 | 自适应参数 | 软评分 |

## 相邻目录边界

- `docs/design-v2/01-system/`：定义系统总语义与优先级。
- `docs/design-v2/02-modules/`：定义模块接口、职责与数据边界。
- `docs/Strategy/`：定义理论来源与方法论映射。
- `docs/spec/`：定义版本证据、路线图、records 与当前状态。
- `docs/observatory/`：定义评审标准与观察框架。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-v2/02-modules/selector-design.md`
- `docs/design-v2/02-modules/strategy-design.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
- `docs/Strategy/README.md`




