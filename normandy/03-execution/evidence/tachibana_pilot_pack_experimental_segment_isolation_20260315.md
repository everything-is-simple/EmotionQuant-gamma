# Tachibana Pilot-Pack Experimental-Segment Isolation

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana pilot-pack experimental-segment isolation formal readout`

---

## 1. 目标

`N3m` 要回答的不是“再跑什么新矩阵”，而是：

`当前 pilot-pack 里，哪些结果只能作为 experimental sidecar，绝不能混进 canonical aggregate。`

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/30-phase-n3m-tachibana-pilot-pack-experimental-segment-isolation-card-20260315.md`
2. `normandy/03-execution/evidence/tachibana_pilot_pack_implementation_scaffold_20260315.md`
3. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
4. `normandy/03-execution/evidence/tachibana_pilot_pack_unit_regime_overlay_20260315.md`
5. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
6. `normandy/03-execution/records/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-record-20260315.md`
7. `src/backtest/normandy_tachibana_pilot_pack.py`
8. `tests/unit/backtest/test_normandy_tachibana_pilot_pack.py`

---

## 3. Formal Isolation Rule

`N3m` 当前正式写死的隔离语义是：

1. `canonical aggregate` 当前只允许包含：
   - `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0`
   - `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0`
2. 以下结果只能进入 `experimental sidecar`，不能并入 canonical aggregate：
   - `cooldown family` 的 `CD2 / CD5 / CD10`
   - `unit regime overlay` 的 `single_lot floor lines`
   - 显式打开时的 `noncanonical fixed-notional side references`
3. `experimental_segment_policy = isolate_from_canonical_aggregate` 是治理边界，不是新交易逻辑

---

## 4. Code-Level Landing

### 4.1 matrix payload 继续只负责写出 policy

当前 `matrix payload` 已继续贯穿：

1. `experimental_segment_policy`
2. `unit_regime_tag`
3. `reduced_unit_scale`

这说明 `matrix` 负责把身份写出来，但不在这一层做 aggregate promotion。

### 4.2 digest 现在正式隔离 canonical aggregate 与 sidecar

`src/backtest/normandy_tachibana_pilot_pack.py` 当前已补出显式的 `experimental_segment_isolation` 摘要，正式输出：

1. `canonical_aggregate_labels`
2. `experimental_sidecar_labels`
3. `cooldown_sidecar_labels`
4. `unit_regime_sidecar_labels`
5. `noncanonical_fixed_notional_reference_labels`
6. `forbidden_canonical_merge_groups`

因此 `digest` 不再只是“顺手带一个 policy tag”，而是明确告诉我们：

`哪些结果能进主结论，哪些只能旁路展示。`

### 4.3 `E1 formal-entry digest` 不再让 side references 污染 leader

`N3m` 当前最关键的实现收口是：

`_build_e1_digest_payload()` 现在只允许 canonical pair 进入 formal-entry digest。`

这意味着：

1. `TRAIL_SCALE_OUT_33_67 / TRAIL_SCALE_OUT_50_50` 即使显式跑了，也只能留在 sidecar
2. 它们不能反写 `E1 leader`
3. `cooldown rows` 也不能混入 `E1` 的 canonical pair ranking

---

## 5. Current Boundary Table

| 结果类型 | 当前身份 | 能否并入 canonical aggregate | 当前正确去处 |
|---|---|---|---|
| `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0` | canonical control | `yes` | `E1 formal-entry digest` |
| `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0` | canonical proxy | `yes` | `E1 formal-entry digest` |
| `CD2 / CD5 / CD10` cooldown rows | experimental cooldown sidecar | `no` | `cooldown_scorecard` |
| `single_lot floor lines` | experimental unit-regime sidecar | `no` | `floor_sanity_summary` |
| `TRAIL_SCALE_OUT_33_67 / 50_50` 等 side refs | experimental proxy-reference sidecar | `no` | `side_reference_comparison` |

---

## 6. What This Does And Does Not Prove

当前已经证明的：

1. `experimental_segment_policy` 不再只是空标签
2. digest 已经能显式区分 canonical aggregate 与 experimental sidecar
3. 非 canonical 结果当前不能再污染 `E1 leader`

当前仍然没有证明的：

1. 任何 experimental sidecar 已具备 mainline promotion 资格
2. `CD10` 已可升格为默认 cooldown
3. `TRAIL_SCALE_OUT_33_67 / 50_50` 已可并入 canonical pair
4. `reduced_unit_scale` 已经成为 executable sizing

---

## 7. 一句话结论

`N3m` 把 Tachibana pilot-pack 的实验段隔离正式写死了：当前只有 canonical control/proxy pair 能进入主 aggregate，cooldown、floor、以及非 canonical proxy reference 全都只能走 experimental sidecar。
