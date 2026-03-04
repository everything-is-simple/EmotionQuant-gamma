# docs 目录导航

## 目录定位

`docs/` 只承担文档归档与检索，不放运行时代码。

## 子目录职责

1. `design-v2/`
   - 系统级总纲与模块级设计。
   - 唯一系统总纲入口：`design-v2/system-baseline.md`。
   - 不放分阶段路线图和实现卡。
2. `spec/`
   - 各阶段全量归档（`v0.01+`）。
   - 每个阶段一个子目录：`spec/<version>/`。
   - 可包含：路线图、实现卡、runbook、勘误、发布记录、评审证据。
3. `reference/`
   - 外部参考资料、方法论记录、第三方材料。
   - 不作为系统执行口径的权威来源。

## 阅读顺序

1. 先读 `design-v2/system-baseline.md`（系统口径）。
2. 再读 `spec/<version>/`（对应阶段落地细化）。
3. 需要背景资料时查 `reference/`。
