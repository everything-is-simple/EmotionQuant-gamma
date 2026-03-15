# Phase N3m Tachibana Pilot-Pack Experimental-Segment Isolation Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3m`  
**对象**: `Tachibana pilot-pack experimental-segment isolation formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3m / Tachibana pilot-pack experimental-segment isolation` 的正式裁决写死。  
这张 record 只回答 5 件事：

1. 当前 `experimental_segment_policy` 的正式语义是什么
2. 哪些结果当前只能作为 `experimental sidecar`
3. 哪些 aggregate 明确禁止并入 canonical 主结论
4. `E1 formal-entry digest` 是否已经挡住 side-reference 污染
5. 下一张主队列卡应如何推进

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_experimental_segment_isolation_20260315.md`
2. `normandy/03-execution/evidence/tachibana_pilot_pack_implementation_scaffold_20260315.md`
3. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
4. `normandy/03-execution/evidence/tachibana_pilot_pack_unit_regime_overlay_20260315.md`
5. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
6. `normandy/03-execution/records/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-record-20260315.md`
7. `src/backtest/normandy_tachibana_pilot_pack.py`
8. `tests/unit/backtest/test_normandy_tachibana_pilot_pack.py`

---

## 3. 正式裁决

`N3m` 的正式裁决固定为：

1. `experimental_segment_policy = isolate_from_canonical_aggregate`
2. 当前 `canonical aggregate` 只允许包含：
   - `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0`
   - `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0`
3. 当前以下对象正式归类为 `experimental sidecar`：
   - `cooldown family`
   - `single_lot floor lines`
   - `noncanonical fixed-notional side references`
4. `E1 formal-entry digest` 当前正式判定为：
   `isolated_from_noncanonical_side_references`
5. 下一张主队列卡固定切向：
   `N3n / Tachibana pilot-pack migration boundary`

---

## 4. 为什么 canonical aggregate 当前只能保留 canonical pair

原因固定为：

1. `N3g` 已把第一工程代理锚点固定为 `TRAIL_SCALE_OUT_25_75`
2. `N3k` 的 cooldown family 本质上是 overlay family，不是默认 pair
3. `N3l` 已把 `single_lot` 正式降为 floor sanity line
4. `N3m` 当前不能允许任何实验段结果反写 `E1 formal-entry digest`

因此当前更诚实的 canonical aggregate 只能是：

`FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0 + TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0`

---

## 5. 为什么 cooldown / floor / side references 只能做 sidecar

三类对象当前都不能混入主 aggregate：

### 5.1 cooldown family

原因：

1. 它们回答的是 `overlay competition`
2. 它们当前正确输出位置是 `cooldown_scorecard`
3. 它们不能反写 `E1` 的 canonical pair 排名

### 5.2 unit-regime floor lines

原因：

1. `single_lot` 当前只保留为 floor sanity
2. `TRAIL_SCALE_OUT_25_75` 在 floor 下已退化
3. 它们当前正确输出位置是 `floor_sanity_summary`

### 5.3 noncanonical fixed-notional side references

原因：

1. 它们只用于 context comparison
2. 它们没有被正式提升为 default pilot anchor
3. 因此即使显式运行，也只能进入 `side_reference_comparison`

---

## 6. 为什么说 `E1 digest` 现在真的被挡住了

`N3m` 的关键实现动作不是新 replay，而是 digest 聚合边界修正：

1. `_build_e1_digest_payload()` 现在只消费 canonical pair
2. `experimental_segment_isolation` 摘要现在会显式列出 sidecar labels
3. `forbidden_canonical_merge_groups` 已正式写出：
   - `e1_formal_entry_digest`
   - `canonical_control_baseline`
   - `operating_proxy_baseline`

因此当前必须正式写死：

`side references can be observed, but cannot contaminate canonical leader selection`

---

## 7. 当前已经回答与仍未回答的

当前已经回答的：

1. `experimental_segment_policy` 当前正式等于 aggregate 隔离
2. 当前 canonical aggregate 的成员已写死
3. cooldown / floor / side refs 的 sidecar 身份已写死
4. `E1 leader` 不再允许被非 canonical 结果污染

当前仍未回答的：

1. 这些治理边界里，哪些适合迁回主线
2. 哪些结论只配留在 Normandy 研究线
3. 这轮 pilot-pack 最终怎样收官

---

## 8. 明确继续挡住的内容

`N3m` 完成后，以下内容继续明确挡住：

1. 把 `CD10` 误写成默认 cooldown
2. 把 `single_lot floor lines` 误写成第二 operating lane
3. 把 `TRAIL_SCALE_OUT_33_67 / 50_50` 误写成 canonical pair 新成员
4. 把 `experimental sidecar` 误写成主线默认参数

---

## 9. 下一张卡

`N3m` 完成后的 next main queue card 固定为：

`N3n / Tachibana pilot-pack migration boundary`

它只允许回答：

1. 当前 pilot-pack 到底有哪些结论能迁回主线
2. 哪些结论只能留在研究线
3. 哪些属于治理边界与负面约束，而不是默认参数

---

## 10. 正式结论

当前 `N3m Tachibana pilot-pack experimental-segment isolation` 的正式结论固定为：

1. canonical aggregate 现在只保留 canonical control/proxy pair
2. cooldown、floor、以及 side references 当前都只能走 experimental sidecar
3. digest 已能显式输出 `experimental_segment_isolation` 摘要
4. `E1 formal-entry digest` 已正式挡住非 canonical side-reference 污染
5. 下一步应进入 `migration boundary`，而不是继续把实验段混写成默认结论

---

## 11. 一句话结论

`N3m` 把 pilot-pack 的实验段隔离正式写死了：能进主 aggregate 的现在只有 canonical pair，其余全都只能旁路展示，不能反写主结论。
