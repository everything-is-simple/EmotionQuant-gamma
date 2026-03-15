# Phase N3n Tachibana Pilot-Pack Migration Boundary Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3n`  
**对象**: `Tachibana pilot-pack migration boundary formal ruling`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3n / Tachibana pilot-pack migration boundary` 的正式裁决写死。  
这张 record 只回答 5 件事：

1. 当前 pilot-pack 到底有哪些东西允许迁回主线
2. 哪些东西只能继续留在 Normandy 研究线
3. 哪些负面约束必须迁回主线作为边界
4. 当前 retained 的到底是 `execution boundary` 还是 `new system`
5. 下一张主队列卡该怎样正式收官

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_migration_boundary_20260315.md`
2. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
3. `normandy/03-execution/evidence/tachibana_pilot_pack_unit_regime_overlay_20260315.md`
4. `normandy/03-execution/evidence/tachibana_pilot_pack_experimental_segment_isolation_20260315.md`
5. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
6. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
7. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
8. `normandy/03-execution/records/27-phase-n3j-tachibana-pilot-pack-runner-implementation-record-20260315.md`
9. `normandy/03-execution/records/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-record-20260315.md`
10. `normandy/03-execution/records/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-record-20260315.md`
11. `normandy/03-execution/records/30-phase-n3m-tachibana-pilot-pack-experimental-segment-isolation-record-20260315.md`
12. `src/backtest/normandy_tachibana_pilot_pack.py`
13. `scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py`
14. `scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`

---

## 3. 正式裁决

`N3n` 的正式裁决固定为：

1. 当前允许迁回主线的，只是 `pilot-pack execution boundary`
2. 当前允许迁回主线的，不是 `full Tachibana system`
3. 当前主线可继承的对象只分三类：
   - `boundary`
   - `execution scaffold`
   - `governance constraint`
4. 当前以下对象继续只配留在 Normandy：
   - `cooldown family ordering`
   - `single_lot floor sanity`
   - `noncanonical side references`
   - `reduced_unit_scale payload tag`
5. 下一张主队列卡固定切向：
   `N3o / Tachibana pilot-pack campaign closeout`

---

## 4. 当前到底能迁回主线什么

### 4.1 boundary

主线当前允许正式继承：

1. 只开 `R4 + R5 + R6 + R7 + R10`
2. 继续冻结 `R2 / R3 / R8 / R9`
3. 不把 pilot-pack 写成完整立花系统

### 4.2 execution scaffold

主线当前允许正式继承：

1. 复用现有 `BOF stack`
2. 保留 `Normandy thin runner` 的实现路径
3. 保留 `same-code cooldown signal_filter hook` 作为 optional scaffold
4. 继续采用 `matrix + digest + sidecar` 的输出层次

### 4.3 governance constraint

主线当前允许正式继承：

1. `TRAIL_SCALE_OUT_25_75` 只能叫 `reduce_to_core engineering proxy`
2. `FIXED_NOTIONAL_CONTROL` 仍是唯一 operating regime
3. canonical aggregate 当前只保留 canonical control/proxy pair
4. cooldown、floor、side references 必须继续隔离在 `experimental sidecar`

---

## 5. 当前明确不能迁什么

以下对象当前必须正式判定为：

`not mainline-migratable`

1. `CD10 = provisional cooldown leader`
2. `CD5 = first effective cooldown`
3. `single_lot floor` 的全套对照线
4. `TRAIL_SCALE_OUT_33_67 / 50_50` 的比较读数
5. `reduced_unit_scale` 的 sizing 想象
6. 任何 `probe -> mother promotion / add-on buy / reduce -> re-add / lock / reverse restart` 叙述

原因固定为：

1. 它们要么还只是研究线发现
2. 要么当前明确受 `ALREADY_HOLDING` 与 mechanism gap 阻塞
3. 要么仍然只是 governance tag，不是 executable default

---

## 6. 哪些东西虽然不能当默认参数，但必须迁成主线边界

这类内容必须正式保留为：

`negative migration constraints`

1. 不宣称“完整立花系统已可验证”
2. 不把 `TRAIL_SCALE_OUT_25_75` 误写成立花真身
3. 不把 `CD10` 误写成默认 cooldown
4. 不把 `single_lot` 误写成第二 operating lane
5. 不把 `reduced_unit_scale` 误写成已落地 sizing
6. 不让 partial-exit lane 替 sizing lane 擦屁股

---

## 7. retained 的到底是什么

`N3n` 当前必须明确写死：

我们这轮真正 retained 下来的，是：

`a governed executable boundary on top of the existing BOF stack`

不是：

`a new complete Tachibana trading system`

---

## 8. 当前已经回答与仍未回答的

当前已经回答的：

1. 哪些东西可以迁回主线
2. 哪些东西只能继续留在 Normandy
3. 哪些负面约束必须跟着一起迁回主线
4. 当前 retained 的只是 execution boundary，不是完整系统

当前仍未回答的：

1. 这轮 Normandy Tachibana campaign 应怎样正式收官
2. 收官后未来如果再开，应属于哪类 backlog
3. 哪些内容需要转成长期 mainline migration package

---

## 9. 下一张卡

`N3n` 完成后的 next main queue card 固定为：

`N3o / Tachibana pilot-pack campaign closeout`

它只允许回答：

1. 这一轮 pilot-pack 最终完成了什么
2. 哪些问题明确仍未解决
3. 以后如果继续，只能开什么类型的新卡

---

## 10. 正式结论

当前 `N3n Tachibana pilot-pack migration boundary` 的正式结论固定为：

1. 当前可迁回主线的是 `execution boundary`、`execution scaffold` 与 `governance constraint`
2. 当前不可迁回主线的是 cooldown winners、floor sanity lines、noncanonical side references 与 sizing 想象
3. 当前必须连同主线一起继承的是一组负面约束，而不是一组新默认参数
4. 当前 retained 的不是完整立花系统，而是基于现有 BOF 栈的一套受治理约束的 pilot-pack 边界
5. 下一步应进入 `campaign closeout`，而不是继续把研究线结论抬成主线默认

---

## 11. 一句话结论

`N3n` 把“能迁什么、不能迁什么”正式钉死了：主线能拿走的是边界、承载方式和治理约束，不能拿走的是研究线领先项、代理冒充和完整系统神话。
