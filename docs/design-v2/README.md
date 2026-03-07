# design-v2 目录说明

## 定位

`docs/design-v2/` 只存放系统级设计基线、模块级设计与算法级 SoT，不存放分阶段执行材料。

# design-v2 目录说明

## 定位

`docs/design-v2/` 只存放系统级设计基线、模块级设计与算法级 SoT，不存放分阶段执行材料。

## 结构

```
design-v2/
├── README.md                   # 本文件
│
├── 01-system/                  # 系统级设计
│   ├── system-baseline.md      # 系统基线（单一事实源）⭐
│   └── architecture-master.md  # 架构总览
│
├── 02-modules/                 # 模块级设计
│   ├── data-layer-design.md
│   ├── selector-design.md
│   ├── strategy-design.md
│   ├── broker-design.md
│   └── backtest-report-design.md
│
└── 03-algorithms/              # 算法级 SoT
    └── core-algorithms/
        ├── README.md
        ├── mss-algorithm.md
        ├── irs-algorithm.md
        ├── pas-algorithm.md
        └── down-to-top-integration.md
```

## 口径规则

1. **系统级**（01-system/）：
   - `system-baseline.md`：系统级执行 SoT，最高优先级
   - `architecture-master.md`：架构总览与模块关系

2. **模块级**（02-modules/）：
   - 各模块的详细设计文档
   - 定义模块职责、接口、实现规范

3. **算法级**（03-algorithms/）：
   - MSS/IRS/PAS 算法设计
   - 集成模式与演进路径

4. **分阶段材料归属**：
   - 分阶段文件统一归档到 `docs/spec/<version>/`

## 相关文档

- 评审标准：`docs/observatory/sandbox-review-standard.md`（系统观察与验证）
- 理论基础：`docs/Strategy/`（理论来源与方法论溯源）
- 治理铁律：`docs/steering/`（不可变约束）

## 口径规则

1. `system-baseline.md`：系统级执行 SoT
2. `mss/irs/pas-algorithm.md`：算法级 SoT
3. `docs/spec/<version>/records`：阶段记录与证据
4. `docs/reference/`：历史研究与参考资料

