# Phase N3I Tachibana Pilot-Pack Implementation Scaffold Card

**状态**: `Active`  
**日期**: `2026-03-15`  
**对象**: `Tachibana pilot-pack implementation scaffold`

---

## 1. 定位

`N3i` 负责把 executable matrix 压成最小实现骨架。  
它不讨论“该不该做”，只讨论：

`代码最小该怎么落。`

---

## 2. 开工前提

1. `normandy/03-execution/25-phase-n3h-tachibana-pilot-pack-executable-matrix-card-20260315.md`
2. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`

---

## 3. 当前目标

1. 固定 `E1` 的 runner 入口
2. 固定 `E2` 的 cooldown hook 位点
3. 固定 `E3` 的 tag/report glue
4. 写死哪些核心层不动

---

## 4. 固定边界

1. 不重写 Broker
2. 不碰 `ALREADY_HOLDING`
3. 不把 `reduced_unit` 升格成新 sizing lane

---

## 5. 任务拆解

### N3I-1 Runner Scaffold

目标：

1. 给 `E1` 指定 thin runner
2. 给 matrix/digest 入口定名

### N3I-2 Hook Scaffold

目标：

1. 把 cooldown 固定挂到 `run_backtest() -> broker.process_signals()` 之间
2. 不改 Broker 核心语义

### N3I-3 Payload Scaffold

目标：

1. 把 `unit_regime_tag / reduced_unit_scale / experimental_segment_policy` 只先贯穿到 payload

---

## 6. 出场条件

1. 已落 implementation scaffold
2. 已明确新增文件与最小改动位点
3. 已把下一步切到 `N3j / runner implementation`

---

## 7. 一句话任务

`把 E1-E3 压成最小实现骨架，明确哪些层能动，哪些层别碰。`
