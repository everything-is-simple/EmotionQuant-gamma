# design-v2 目录说明

## 定位

`docs/design-v2/` 只存放系统级设计基线、模块级设计与算法级 SoT，不存放分阶段执行材料。

## 结构

1. 系统基线（SoT）
   - `system-baseline.md`
2. 算法级 SoT
   - `core-algorithms/mss-algorithm.md`
   - `core-algorithms/irs-algorithm.md`
   - `core-algorithms/pas-algorithm.md`
   - `core-algorithms/down-to-top-integration.md`
   - `core-algorithms/README.md`
3. 模块级设计
   - `architecture-master.md`
   - `data-layer-design.md`
   - `selector-design.md`
   - `strategy-design.md`
   - `broker-design.md`
   - `backtest-report-design.md`
4. 阶段材料归属
   - 分阶段文件统一归档到 `docs/spec/<version>/`

## 相关文档

- 评审标准：`docs/observatory/sandbox-review-standard.md`（系统观察与验证）
- 理论基础：`docs/Strategy/`（理论来源与方法论溯源）

## 口径规则

1. `system-baseline.md`：系统级执行 SoT
2. `mss/irs/pas-algorithm.md`：算法级 SoT
3. `docs/spec/<version>/records`：阶段记录与证据
4. `docs/reference/`：历史研究与参考资料

