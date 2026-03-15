# Tachibana Pilot-Pack Campaign Closeout

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana pilot-pack campaign closeout map and future backlog`

---

## 1. 目标

`N3o` 要回答的不是“下一步再补什么实验”，而是：

`这轮 Tachibana pilot-pack 到底完成了什么、没完成什么、以后若继续只能怎么再开。`

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/records/17-phase-n3-tachibana-tradebook-contract-record-20260315.md`
2. `normandy/03-execution/records/18-phase-n3a-tachibana-january-sample-blocker-record-20260315.md`
3. `normandy/03-execution/records/19-phase-n3b-tachibana-rear-pages-source-correction-record-20260315.md`
4. `normandy/03-execution/records/20-phase-n3c-tachibana-semantics-and-replay-ledger-record-20260315.md`
5. `normandy/03-execution/records/21-phase-n3d-emotionquant-module-reuse-triage-record-20260315.md`
6. `normandy/03-execution/records/22-phase-n3e-tachibana-state-transition-candidate-table-record-20260315.md`
7. `normandy/03-execution/records/23-phase-n3f-tachibana-validation-rule-candidate-matrix-record-20260315.md`
8. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
9. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
10. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
11. `normandy/03-execution/records/27-phase-n3j-tachibana-pilot-pack-runner-implementation-record-20260315.md`
12. `normandy/03-execution/records/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-record-20260315.md`
13. `normandy/03-execution/records/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-record-20260315.md`
14. `normandy/03-execution/records/30-phase-n3m-tachibana-pilot-pack-experimental-segment-isolation-record-20260315.md`
15. `normandy/03-execution/records/31-phase-n3n-tachibana-pilot-pack-migration-boundary-record-20260315.md`
16. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
17. `normandy/03-execution/evidence/tachibana_pilot_pack_unit_regime_overlay_20260315.md`
18. `normandy/03-execution/evidence/tachibana_pilot_pack_experimental_segment_isolation_20260315.md`
19. `normandy/03-execution/evidence/tachibana_pilot_pack_migration_boundary_20260315.md`
20. `src/backtest/normandy_tachibana_pilot_pack.py`
21. `scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py`
22. `scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`

---

## 3. Campaign Map

这轮 `Tachibana pilot-pack` 的正式地图可以压成 4 段：

| 战役段 | 回答的问题 | 正式产出 | 当前结论 |
|---|---|---|---|
| `N3 ~ N3f` | 我们到底在验证什么，哪些规则现在可用 | tradebook contract、语义 ledger、候选状态表、rule matrix | 当前只诚实打开 `R4 + R5 + R6 + R7 + R10` |
| `N3g ~ N3j` | 当前可迁回子集怎样真正挂到现有 BOF 栈上跑 | opening note、executable matrix、implementation scaffold、runner implementation | 当前 pilot-pack 已具备正式 matrix/digest/runner 入口 |
| `N3k ~ N3m` | cooldown、unit regime、experimental segment 应如何治理 | formal cooldown matrix、unit-regime overlay、segment isolation | `CD10` 仍只是 provisional leader；`single_lot` 只是 floor；sidecar 不准污染 canonical aggregate |
| `N3n` | 当前哪些东西能迁回主线 | migration boundary | 只能迁 `boundary + scaffold + governance constraint`，不能迁实验领先项 |

---

## 4. What This Campaign Actually Solved

这轮 pilot-pack 真正解决掉的事，正式固定为：

1. 把 “立花方法” 从口头理解压成了 `truth-source + candidate-rule + replay-boundary`
2. 把当前仓库里能诚实开跑的子集正式收窄成 `pilot-pack`
3. 把 `pilot-pack` 挂到了现有 `BOF stack` 上，不需要再写第二套新引擎
4. 把 `same-code cooldown hook`、`unit_regime tag`、`experimental sidecar isolation` 都落成了正式治理结构
5. 把当前能迁回主线的东西收窄成：边界、承载方式、治理约束

一句话说：

`这轮战役完成的是“把可执行边界钉死”，不是“把完整立花系统做出来”。`

---

## 5. What This Campaign Explicitly Did Not Solve

这轮 pilot-pack 明确没有解决的事，正式固定为：

1. 没有证明“完整立花系统已经 ready”
2. 没有打通 `probe -> mother promotion`
3. 没有打通同向加码、`reduce -> re-add`、锁单、反向再出发
4. 没有把 `CD10` 提升成默认 cooldown
5. 没有把 `TRAIL_SCALE_OUT_25_75` 提升成立花正式语义
6. 没有把 `single_lot` 变成第二 operating lane
7. 没有把 `reduced_unit_scale` 变成 executable sizing

这些没解决，不是遗漏，而是当前被正式挡住：

`blocked by mechanism gap or governance boundary`

---

## 6. Mainline Migration Summary

当前能迁回主线的正式摘要如下：

1. `pilot-pack != full Tachibana system`
2. 当前主线只可引用 `R4 + R5 + R6 + R7 + R10 only` 的 executable boundary
3. 当前主线只可复用 `existing BOF stack + Normandy thin runner + optional signal_filter hook`
4. 当前主线必须继续守住：
   - `TRAIL_SCALE_OUT_25_75 = engineering proxy only`
   - `FIXED_NOTIONAL_CONTROL = only operating regime`
   - `cooldown/floor/side references = experimental sidecar only`
   - `partial-exit lane does not repair sizing lane`

---

## 7. Future Backlog Gate

`N3o` 收官后，如果未来还要继续开 Tachibana 线，只允许两种开法：

1. `explicit mainline migration package`
   - 用于把已经足够硬的治理边界迁入主线 SoT
2. `new targeted mechanism hypothesis`
   - 用于正面解决当前仍被挡住的机制缺口，例如 `ALREADY_HOLDING` 约束下的 add-on / re-add / reverse restart

这意味着未来不允许：

1. 续跑旧卡
2. 无假设重扫参数
3. 把 sidecar 结果偷抬成默认项

---

## 8. Permanent No-Fake List

收官后，以下内容继续永久挡住：

1. 不宣称“完整立花系统已可验证”
2. 不把 `TRAIL_SCALE_OUT_25_75` 冒充成立花真身
3. 不把 `CD10` 冒充成默认 cooldown
4. 不把 `single_lot floor sanity` 冒充成 operating lane
5. 不把 `reduced_unit_scale` 冒充成 sizing implementation
6. 不把 `experimental sidecar` 冒充成 canonical aggregate

---

## 9. 一句话结论

`N3o` 把这轮 Tachibana pilot-pack 正式收官了：做成的是一套受治理约束的可执行边界，没做成的仍然明确挡住，今后若继续只能新开 migration package 或 targeted mechanism hypothesis。
