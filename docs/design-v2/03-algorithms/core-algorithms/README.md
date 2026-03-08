# 核心算法设计（算法级 SoT）

**版本**: `v0.01-v0.06 设计入口`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `算法语义变更必须同时具备设计修订与证据支撑；若触及系统执行语义，以上游 baseline 为准。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

## 定位

`docs/design-v2/03-algorithms/core-algorithms/` 存放 MSS / IRS / PAS 的当前算法级设计，以及跨版本集成模式说明。

这里回答的是“当前算法怎么算”，不是“理论来源在哪里”或“证据放在哪里”。跨模块执行语义以 `docs/design-v2/01-system/system-baseline.md` 为准；当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准；阶段证据与版本验收统一归档到 `docs/spec/`。

说明：

1. 当前主线稳定设计只保留 5 个关键对象：`Selector / PAS-trigger / IRS-lite / MSS-lite / Broker / Risk`
2. 本目录只负责其中 3 个算法对象：`PAS-trigger / IRS-lite / MSS-lite`
3. `Selector` 与 `Broker / Risk` 的当前主线边界在 `docs/design-v2/02-modules/`
4. 恢复骨架不等于恢复旧语义；所有当前文档必须服从主线：`Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行`

## 当前入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 系统基线 | `docs/design-v2/01-system/system-baseline.md` | 确认跨模块执行语义与总边界 |
| Selector 当前主线 | `docs/design-v2/02-modules/selector-mainline-design.md` | 查看当前主线初选边界 |
| PAS-trigger / BOF | `pas-algorithm.md` | 查看当前主线形态触发职责 |
| IRS-lite | `irs-algorithm.md` | 查看当前主线行业排序增强职责 |
| MSS-lite | `mss-algorithm.md` | 查看当前主线市场级风险覆盖职责 |
| Broker / Risk 当前主线 | `docs/design-v2/02-modules/broker-risk-mainline-design.md` | 查看当前主线执行边界 |
| MSS 数据模型 | `mss-data-models.md` | 查看 MSS 输入、输出与执行层派生模型 |
| MSS 接口契约 | `mss-api.md` | 查看 MSS 计算入口与 Broker 消费接口 |
| MSS 信息流 | `mss-information-flow.md` | 查看 MSS 在 DTT 主线中的落库与风险消费链路 |
| IRS 数据模型 | `irs-data-models.md` | 查看 IRS 表结构、字段与扩展口径 |
| IRS 接口契约 | `irs-api.md` | 查看 IRS 输入输出、异常与消费方式 |
| IRS 信息流 | `irs-information-flow.md` | 查看 IRS 在 DTT 主线中的数据流与边界 |
| PAS 数据模型 | `pas-data-models.md` | 查看 formal signal、sidecar 与 detector 输入输出 |
| PAS 接口契约 | `pas-api.md` | 查看 detector / registry / strategy 主入口 |
| PAS 信息流 | `pas-information-flow.md` | 查看 PAS 从候选池到 formal signal 的链路 |
| 集成模式 | `down-to-top-integration.md` | 查看 v0.01-plus 当前主线的集成骨架 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 查看当前治理阶段与重启条件 |

## 结构

```text
core-algorithms/
├── README.md                    # 本文件
├── mss-algorithm.md             # MSS 当前算法口径
├── mss-data-models.md           # MSS 数据模型
├── mss-api.md                   # MSS 接口契约
├── mss-information-flow.md      # MSS 信息流
├── irs-algorithm.md             # IRS 当前算法口径
├── irs-data-models.md           # IRS 数据模型
├── irs-api.md                   # IRS 接口契约
├── irs-information-flow.md      # IRS 信息流
├── pas-algorithm.md             # PAS 当前算法口径
├── pas-data-models.md           # PAS 数据模型
├── pas-api.md                   # PAS 接口契约
├── pas-information-flow.md      # PAS 信息流
└── down-to-top-integration.md   # 集成模式与演进边界
```

## 使用规则

1. 本目录是算法级 SoT；若与模块设计、理论研究或评审附录冲突，先回到 `docs/design-v2/01-system/system-baseline.md` 判断总边界。
2. 理论来源与采用理由放在 `docs/Strategy/`，不在本目录重复展开研究材料。
3. 版本证据、回测结果、消融实验与验收结论，统一进入 `docs/spec/<version>/evidence/` 或对应 records。
4. 当前是否继续推进 `v0.01` 实现，不在本目录维护，统一查看 `docs/spec/common/records/development-status.md`。
5. 算法语义变更必须同时具备设计修订与证据支撑，不接受只改 README 或只改代码。
6. 当前主线算法正文统一采用 6 段结构：职责、输入、输出契约、不负责什么、决策规则/算法、失败模式与验证证据。
7. 恢复 `beta` 的文档骨架时，只恢复结构和必要设计深度，不恢复已经被当前主线淘汰的 top-down 语义。

## 当前版本范围

| 版本 | MSS | IRS | PAS | 集成模式 |
|---|---|---|---|---|
| v0.01 | 三态硬门控 | Top-N 硬过滤 | BOF 单形态闭环 | Top-Down |
| v0.01-plus | 市场级控仓位 | IRS-lite 排序增强 | BOF detector + DTT sidecar | Down-to-Top |
| v0.02 | 风险状态机增强 | 轮动层 + 基因层 | BOF + BPB | Down-to-Top |
| v0.03 | 动态风险覆盖 | 行业内结构增强 | TST / PB | Down-to-Top |
| v0.04 | 动态仓位带 | 生命周期增强 | CPB + 失败处理 | Down-to-Top |
| v0.05-v0.06 | 自适应阈值 | 自适应权重 | 形态强度 / 自适应参数 | Down-to-Top |

## 相邻目录边界

- `docs/design-v2/01-system/`：定义系统总语义与优先级。
- `docs/design-v2/02-modules/`：定义模块接口、职责与数据边界。
- `docs/Strategy/`：定义理论来源与方法论映射。
- `docs/spec/`：定义版本证据、路线图、records 与当前状态。
- `docs/observatory/`：定义评审标准与观察框架。

## 相关文档

- `docs/design-v2/01-system/system-baseline.md`
- `docs/design-v2/02-modules/selector-mainline-design.md`
- `docs/design-v2/02-modules/broker-risk-mainline-design.md`
- `docs/spec/common/records/development-status.md`
- `docs/spec/README.md`
- `docs/Strategy/README.md`
- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md`
