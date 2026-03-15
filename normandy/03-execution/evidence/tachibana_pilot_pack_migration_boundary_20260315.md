# Tachibana Pilot-Pack Migration Boundary

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana pilot-pack migration boundary formal note`

---

## 1. 目标

`N3n` 要回答的不是“再做哪种新实验”，而是：

`当前 Tachibana pilot-pack 已经产出的东西里，哪些能迁回主线，哪些只能留在 Normandy 研究线。`

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
2. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
3. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
4. `normandy/03-execution/records/27-phase-n3j-tachibana-pilot-pack-runner-implementation-record-20260315.md`
5. `normandy/03-execution/records/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-record-20260315.md`
6. `normandy/03-execution/records/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-record-20260315.md`
7. `normandy/03-execution/records/30-phase-n3m-tachibana-pilot-pack-experimental-segment-isolation-record-20260315.md`
8. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
9. `normandy/03-execution/evidence/tachibana_pilot_pack_unit_regime_overlay_20260315.md`
10. `normandy/03-execution/evidence/tachibana_pilot_pack_experimental_segment_isolation_20260315.md`
11. `src/backtest/normandy_tachibana_pilot_pack.py`
12. `scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py`
13. `scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`

---

## 3. Migration Boundary Table

| 对象 | 当前正式身份 | 是否可迁回主线 | 正确迁移形态 |
|---|---|---|---|
| `R4 + R5 + R6 + R7 + R10 only` pilot boundary | executable boundary | `yes` | 作为 `pilot-pack entry gate` 与负面约束进入主线治理文档 |
| `BOF stack reuse + Normandy thin runner` | implementation reuse pattern | `yes` | 作为 `existing BOF stack wrapper pattern` 进入主线实现说明 |
| `TRAIL_SCALE_OUT_25_75 = reduce_to_core engineering proxy` | engineering proxy only | `yes, limited` | 只能以 `temporary engineering proxy` 身份迁移，不能改写 Tachibana 正式语义 |
| `FIXED_NOTIONAL_CONTROL = only operating regime` | current operating baseline | `yes` | 作为当前唯一 operating regime 进入主线边界说明 |
| `same-code cooldown signal_filter hook` | optional execution hook | `yes, limited` | 只能以 `optional hook scaffold` 身份迁移，不能自动升级成默认 cooldown |
| `experimental_segment_policy = isolate_from_canonical_aggregate` | governance/reporting boundary | `yes` | 作为 aggregate 隔离约束进入主线 digest/report discipline |
| `CD5 / CD10 cooldown family ordering` | experimental overlay finding | `no` | 继续留在 Normandy `cooldown_scorecard` |
| `single_lot floor sanity lines` | floor sanity only | `no` | 继续留在 Normandy `floor_sanity_summary` |
| `TRAIL_SCALE_OUT_33_67 / 50_50` 等 side references | side reference comparison | `no` | 继续留在 `experimental sidecar` |
| `reduced_unit_scale` | payload/governance tag | `no` | 继续保留为 tag，不迁为 executable sizing |
| `R2 / R3 / R8 / R9` | blocked mechanism set | `no` | 继续冻结，等待新的 targeted mechanism card |
| `full Tachibana system` claim | forbidden statement | `no` | 永久禁止迁移成当前主线叙述 |

---

## 4. Migration Note To Mainline

`N3n` 当前允许迁回主线的，不是“一套新的立花系统”，而是三类收窄后的东西：

### 4.1 可以迁的是边界

主线现在可以正式继承：

1. 当前只开 `R4 + R5 + R6 + R7 + R10`
2. 当前继续冻结 `R2 / R3 / R8 / R9`
3. 当前不允许把 pilot-pack 叙述成完整 Tachibana system

这意味着主线继承的是：

`honest execution boundary`

而不是：

`full method promotion`

### 4.2 可以迁的是实现承载方式

主线现在可以正式继承：

1. 用现成 BOF 栈承载 pilot-pack，不重写第二套引擎
2. `same-code cooldown signal_filter hook` 作为可选执行挂点保留
3. `matrix + digest + sidecar` 的输出分层继续沿用

这意味着主线继承的是：

`execution scaffold`

而不是：

`new mechanism default`

### 4.3 可以迁的是治理约束

主线现在可以正式继承：

1. canonical aggregate 当前只保留 canonical control/proxy pair
2. cooldown、floor、side references 继续隔离在 `experimental sidecar`
3. `TRAIL_SCALE_OUT_25_75` 只能叫 `engineering proxy`
4. `FIXED_NOTIONAL_CONTROL` 仍是唯一 operating regime

这意味着主线继承的是：

`governance discipline`

而不是：

`parameter promotion`

---

## 5. What Must Stay In Normandy

以下内容当前必须继续留在 Normandy 研究线，不能迁成主线默认项：

1. `CD10` 作为 provisional cooldown leader 的研究结论
2. `CD5` 作为 first effective cooldown 的研究结论
3. `single_lot` 作为 floor sanity 的验证副线
4. `TRAIL_SCALE_OUT_33_67 / 50_50` 的 side reference 对比
5. `reduced_unit_scale` 的 payload/governance 观察标签

这些对象都还在回答：

`研究线如何看实验结果`

而不是：

`主线今天默认怎么跑`

---

## 6. Negative Constraints That Must Migrate As Constraints

有一类东西虽然不能迁成默认参数，但必须迁回主线作为负面约束：

1. 不宣称“完整立花系统已可验证”
2. 不把 `TRAIL_SCALE_OUT_25_75` 写成立花正式语义替代
3. 不把 `CD10` 写成默认 cooldown
4. 不把 `single_lot floor sanity` 写成第二 operating lane
5. 不把 `reduced_unit_scale` 写成已落地 sizing
6. 不让 partial-exit lane 替 sizing lane 擦屁股

---

## 7. Mainline-Ready Summary

当前 `pilot-pack` 能迁回主线的正式摘要可压成下面 4 句话：

1. 当前主线只允许引用 `pilot-pack executable boundary`，不能引用完整立花系统叙事
2. 当前主线只允许复用 `existing BOF stack + optional hook scaffold`
3. 当前主线只允许把 `TRAIL_SCALE_OUT_25_75` 当作 `reduce_to_core engineering proxy`
4. 当前主线必须继续把 cooldown、floor、以及非 canonical side references 隔离在 sidecar

---

## 8. 一句话结论

`N3n` 把 pilot-pack 的迁移边界正式写死了：能迁回主线的是边界、承载方式和治理约束，不能迁回去的是实验结果、代理语义冒充和完整系统叙事。
