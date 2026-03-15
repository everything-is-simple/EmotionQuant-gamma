# Phase N3J Tachibana Pilot-Pack Runner Implementation Card

**状态**: `Active`  
**日期**: `2026-03-15`  
**对象**: `Tachibana pilot-pack runner implementation`

---

## 1. 定位

`N3j` 是真正把 pilot-pack 跑起来的实现卡。  
它回答的是：

`runner、digest、signal_filter hook 到底怎么正式落库。`

---

## 2. 开工前提

1. `normandy/03-execution/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-card-20260315.md`
2. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`

---

## 3. 当前目标

1. 落 `matrix runner`
2. 落 `digest runner`
3. 落 `signal_filter hook`
4. 跑最小 smoke

---

## 4. 固定边界

1. 不碰非 pilot-pack 主线
2. 不把 smoke 当 formal readout
3. 不解锁被挡住的立花规则

---

## 5. 任务拆解

### N3J-1 Runner Implementation

目标：

1. 正式落 `run_normandy_tachibana_pilot_pack_matrix.py`
2. 正式落 `run_normandy_tachibana_pilot_pack_digest.py`

### N3J-2 Hook Implementation

目标：

1. 落 same-code cooldown filter
2. 让 metrics 进入 matrix/digest payload

### N3J-3 Smoke Readout

目标：

1. 跑一版短窗 smoke
2. 证明链路已接通

---

## 6. 出场条件

1. 已落 runner 与 hook
2. 已有最小 smoke evidence
3. 已把下一步切到 `N3k / formal cooldown matrix`

---

## 7. 一句话任务

`把 pilot-pack 的入口和钩子真正写进仓库，再用短窗 smoke 验链路。`
