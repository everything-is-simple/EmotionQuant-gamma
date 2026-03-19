# GX22 / 回测缓存与批量回放加速卡
**状态**: `Proposal`
**日期**: `2026-03-20`
**类型**: `backtest acceleration`
**直接目标目录**: [`../../src/backtest/`](../../src/backtest/)

---

## 1. 目标

这张卡只回答一个问题：

`当前回测链怎样改，才能少重复 IO、少重复构建，更接近 qlib 那种“先特征、后批量回放”的效率形态？`

---

## 2. 当前瓶颈

1. 多场景 runner 重复开库、清表、跑同一窗口
2. Gene / L3 常被不同场景重复重建
3. 回测主循环按交易日调度，但前置特征没有充分缓存
4. scenario replay 与 feature build 还没有彻底解耦

---

## 3. 本卡必须交付

1. 特征缓存层设计
2. signal matrix 或 replay input cache 设计
3. scenario 共享只读特征库的运行方式
4. 性能 benchmark
5. 与现有 broker 语义兼容的迁移方案

---

## 4. 关闭标准

1. 同窗口多场景回测不再重复重建同一份 L3
2. 研究 runner 能复用同一份回测缓存
3. 速度提升有 formal benchmark 支撑

---

## 5. 一句话收口

`GX22` 要解决的不是单点小优化，而是把回测从“重复读写型 runner”改成“缓存驱动型批量回放”。
