# GX15 / 市场寿命框架总重构包
**状态**: `Active`  
**日期**: `2026-03-19`  
**类型**: `full gene reconstruction package`  
**直接目标目录**: [`../`](../)

---

## 1. 目标

这张卡只回答一个问题：

`如何以《专业投机原理》的趋势定义、趋势改变与市场寿命框架为根基，完成整个 Gene 的下一轮总重构，而不是只修补一个 duration 字段。`

---

## 2. 上游输入

1. [`../01-full-design/03-book-core-trend-and-market-lifespan-framework-freeze-20260319.md`](../01-full-design/03-book-core-trend-and-market-lifespan-framework-freeze-20260319.md)
2. [`../02-implementation-spec/02-market-lifespan-framework-implementation-spec-20260319.md`](../02-implementation-spec/02-market-lifespan-framework-implementation-spec-20260319.md)
3. `50 ~ 58 / 68 ~ 85 / 156 ~ 167 / 341 ~ 350` 页指定书页
4. 图 `11-1` 与图 `26-1`

---

## 3. 本包要解决的四个总问题

1. 趋势定义是否彻底收口：
   - `LONG / INTERMEDIATE / SHORT`
   - `MAINSTREAM / COUNTERTREND`
2. 趋势改变对象是否彻底收口：
   - `trendline break`
   - `1-2-3`
   - `2B`
3. 寿命框架是否彻底收口：
   - `duration`
   - `magnitude`
   - `quartile distribution`
   - `average lifespan / odds`
4. Gene 的下游运行与统计卡，是否全部改读同一套 surface

---

## 4. 本包拆分

### 4.1 设计冻结

必须先补：

1. 书义核心定义冻结
2. 实现映射说明

### 4.2 代码重构

必须继续推进：

1. 趋势层级合同
2. trend change 事件合同
3. lifespan surface 合同
4. quartile / odds surface

### 4.3 执行重审

必须重开：

1. `GX13`
2. `17.8`
3. 后续必要时的 `17.9`

### 4.4 记录与证据

必须留下：

1. 设计变更记录
2. 实现记录
3. rerun evidence

---

## 5. 本包当前阶段顺序

当前固定顺序为：

1. 先读书并冻结概念定义
2. 再写实现映射与总包计划
3. 再改代码
4. 再重跑统计层与 Phase 9
5. 最后补 closeout record

---

## 6. 当前已完成部分

本包当前已完成的前置动作：

1. 已完成关键书页首轮复核
2. 已落盘定义冻结与实现映射
3. 已完成第一版 quartile surface 代码修正
4. 已完成 `GX16 / average lifespan odds surface`
5. `tests/unit/selector/test_gene.py` 已通过

---

## 7. 当前未完成部分

本包尚未完成的关键部分：

1. `GX13` 还没在新 surface 上重跑
2. `17.8` 还没在新 surface 上落正式 evidence
3. 相关 design / execution README 还未全部回灌

---

## 8. 一句话状态

`GX15` 现在是 Gene 总重构的总包；后面所有设计、实现、重跑和记录，都要围绕这套市场寿命框架统一推进。`
