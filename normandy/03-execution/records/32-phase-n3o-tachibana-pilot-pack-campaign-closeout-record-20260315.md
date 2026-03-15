# Phase N3o Tachibana Pilot-Pack Campaign Closeout Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3o`  
**对象**: `Tachibana pilot-pack campaign closeout formal closure`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3o / Tachibana pilot-pack campaign closeout` 的正式裁决写死。  
这张 record 只回答 5 件事：

1. 这一轮 pilot-pack 最终完成了什么
2. 哪些正式结论已经闭环
3. 哪些问题明确仍未解决
4. 未来若继续，只允许开什么类型的新卡
5. 哪些内容必须永久挡住，避免后人误读成“早就 ready”

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_campaign_closeout_20260315.md`
2. `normandy/03-execution/evidence/tachibana_pilot_pack_migration_boundary_20260315.md`
3. `normandy/03-execution/evidence/tachibana_pilot_pack_experimental_segment_isolation_20260315.md`
4. `normandy/03-execution/evidence/tachibana_pilot_pack_unit_regime_overlay_20260315.md`
5. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
6. `normandy/03-execution/records/17-phase-n3-tachibana-tradebook-contract-record-20260315.md`
7. `normandy/03-execution/records/18-phase-n3a-tachibana-january-sample-blocker-record-20260315.md`
8. `normandy/03-execution/records/19-phase-n3b-tachibana-rear-pages-source-correction-record-20260315.md`
9. `normandy/03-execution/records/20-phase-n3c-tachibana-semantics-and-replay-ledger-record-20260315.md`
10. `normandy/03-execution/records/21-phase-n3d-emotionquant-module-reuse-triage-record-20260315.md`
11. `normandy/03-execution/records/22-phase-n3e-tachibana-state-transition-candidate-table-record-20260315.md`
12. `normandy/03-execution/records/23-phase-n3f-tachibana-validation-rule-candidate-matrix-record-20260315.md`
13. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
14. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
15. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
16. `normandy/03-execution/records/27-phase-n3j-tachibana-pilot-pack-runner-implementation-record-20260315.md`
17. `normandy/03-execution/records/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-record-20260315.md`
18. `normandy/03-execution/records/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-record-20260315.md`
19. `normandy/03-execution/records/30-phase-n3m-tachibana-pilot-pack-experimental-segment-isolation-record-20260315.md`
20. `normandy/03-execution/records/31-phase-n3n-tachibana-pilot-pack-migration-boundary-record-20260315.md`
21. `src/backtest/normandy_tachibana_pilot_pack.py`
22. `scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py`
23. `scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`

---

## 3. 收官判定

当前这轮 `Tachibana pilot-pack` 的收官判定固定为：

1. `all_defined_n3_to_n3o_cards_closed = yes`
2. `all_formal_records_closed = yes`
3. `active_tachibana_pilot_pack_main_queue = none`
4. `future_reentry_requires = explicit_mainline_migration_package_or_new_targeted_mechanism_hypothesis`
5. `full_tachibana_system_ready = no`

这意味着：

`这轮 pilot-pack 不是还有旧卡没跑完，而是当前定义过的卡已经全部闭环。`

---

## 4. 这轮到底完成了什么

`N3o` 当前正式确认，这轮战役完成了 5 件事：

1. 把 Tachibana 相关书面材料压成了 `truth source + replay ledger + candidate rule boundary`
2. 把当前仓库里能诚实开跑的规则收窄成 `R4 + R5 + R6 + R7 + R10`
3. 把 pilot-pack 正式挂回现有 `BOF stack`，并提供 matrix/digest/runner 入口
4. 把 cooldown、unit regime、experimental segment 都降到正确治理位置
5. 把当前可迁回主线的内容正式收窄成 `execution boundary + execution scaffold + governance constraint`

---

## 5. 哪些正式结论已经闭环

当前已经闭环的正式结论固定为：

1. `pilot-pack != full Tachibana system`
2. `TRAIL_SCALE_OUT_25_75 = reduce_to_core engineering proxy only`
3. `FIXED_NOTIONAL_CONTROL = only operating regime`
4. `SINGLE_LOT_CONTROL = floor sanity only`
5. `CD2 = no-op overlay`
6. `CD5 = first effective cooldown`
7. `CD10 = provisional cooldown leader`
8. `experimental sidecar must stay isolated from canonical aggregate`
9. 主线当前只能迁入边界、承载方式和治理约束，不能迁入实验领先项

---

## 6. 哪些问题明确仍未解决

当前仍未解决的内容固定为：

1. `probe -> mother promotion`
2. 同向加码
3. `reduce -> re-add`
4. 锁单
5. 反向再出发
6. `reduced_unit_scale` 的 executable sizing
7. 完整立花系统的可验证实现

原因也已固定：

1. 要么仍受 `ALREADY_HOLDING` 约束阻塞
2. 要么当前没有足够机制承载
3. 要么本轮正式裁决要求继续冻结

---

## 7. 可迁回主线与只能留研究线的最终摘要

### 7.1 可迁回主线

1. `R4 + R5 + R6 + R7 + R10 only` 的 pilot boundary
2. `existing BOF stack + thin runner + optional hook scaffold`
3. `engineering proxy / operating regime / sidecar isolation` 这组治理口径
4. 一整套负面约束：
   - 不冒充完整系统
   - 不冒充默认 cooldown
   - 不冒充第二 operating lane
   - 不冒充 sizing implementation

### 7.2 只能留在研究线

1. cooldown family leader ordering
2. floor sanity 对照线
3. noncanonical proxy side references
4. 任何被挡住的机制段想象

---

## 8. 收官后若未来继续，只能怎么继续

`N3o` 完成后，未来若要继续 Tachibana 线，只允许两种类型的新卡：

1. `explicit mainline migration package`
2. `new targeted mechanism hypothesis`

这意味着未来不允许：

1. 续跑旧 `N3` 卡
2. 做无假设参数再扫
3. 把已冻结对象偷带回主线默认叙事

---

## 9. 继续永久挡住的内容

收官后，以下内容继续永久挡住：

1. 宣称“完整立花系统已可验证”
2. 宣称 `TRAIL_SCALE_OUT_25_75` 就是立花真身
3. 宣称 `CD10` 已经是默认 cooldown
4. 宣称 `single_lot floor` 已经升级成正式 lane
5. 宣称 `reduced_unit_scale` 已经落地成 sizing
6. 宣称 experimental sidecar 已可并入 canonical aggregate

---

## 10. 与旧 Normandy campaign closeout 的关系

这里必须正式写死：

`N3o` 收官的是 `Tachibana pilot-pack sub-campaign`，不是重写或推翻 `2026-03-13 Normandy campaign closeout`。

两者关系是：

1. `2026-03-13` 那张 closeout 收的是 Normandy 前段总战役
2. `N3o` 收的是后续显式新开的 Tachibana pilot-pack 治理段
3. 当前两张 closeout 可以并存，且都成立

---

## 11. 正式结论

当前 `N3o Tachibana pilot-pack campaign closeout` 的正式结论固定为：

1. 当前定义过的 `N3 ~ N3o` cards 已全部闭环
2. 当前定义过的 pilot-pack formal records 已全部闭环
3. 这轮战役完成的是一套受治理约束的可执行 pilot boundary，不是完整立花系统
4. 当前能迁回主线的是边界、承载方式和治理约束，不能迁的是实验领先项和机制空想
5. 未来若继续，只能新开 `explicit mainline migration package` 或 `new targeted mechanism hypothesis`

---

## 12. 一句话结论

`N3o` 把 Tachibana pilot-pack 这一轮正式收官了：该落的边界已经落了，该挡的幻觉继续挡住，后面如果再开，必须新开卡，不再续跑旧战役。
