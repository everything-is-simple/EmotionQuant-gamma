# PAS 理论来源导航

**状态**: `Active`  
**主要归属**: `第二战场上游理论源`

## 定位

`docs/Strategy/PAS/` 保留价格行为、结构触发器和相关映射的上游来源。

这里负责：

1. 保留 `YTC` 五形态及相关价格行为结构语言
2. 保留 `Volman -> YTC -> A股` 的映射思路
3. 说明哪些想法被主线或第二战场吸收，哪些只保留为研究背景

这里不是当前 `PAS` 的正式 SoT。

当前正式设计请看：

- `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
- `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
- `normandy/`
- `../../spec/README.md`
- `../../spec/common/records/development-status.md`
- `../../design-v2/01-system/system-baseline.md`

## 当前入口

- `lance-beggs-ytc-analysis.md`
- `volman-ytc-mapping.md`
- `xu-jiachong-naked-kline-analysis.md`

## 战场边界

1. 主要服务第二战场。
2. 主线 `BOF` 语义也会引用这里的来源背景。
3. 第四战场只能借用其结构语法做条件解释，不能拿 `PAS` 代替趋势和波段的基础定义。
