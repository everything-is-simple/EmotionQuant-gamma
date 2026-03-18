# GX4 Evidence: mainstream / countertrend 语义整改验证

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 证据来源

1. 配套 record：`records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md`
2. 本文件只整理 record 中已固化的语义变更点与验证结果

---

## 2. 语义整改证据

1. `wave_role` 现在先相对于 `context_trend_direction_before` 判定
2. `wave_role` 不再因为本 wave 自己翻转 `trend_direction_after` 就回洗成 `MAINSTREAM`
3. 正式 basis 已从 `INTERMEDIATE_MAJOR_TREND_PROXY` 更新为 `INTERMEDIATE_PARENT_CONTEXT_DIRECTION`
4. `current_wave_role / current_wave_role_basis` 已与 `l3_gene_wave.wave_role` 共用同一套父趋势参照逻辑

---

## 3. 验证命令证据

1. `python -m pytest tests/unit/selector/test_gene.py -q`
   - `4 passed`
2. `python -m py_compile src/selector/gene.py tests/unit/selector/test_gene.py`
   - `通过`

---

## 4. Evidence verdict

当前证据支持：

1. `mainstream / countertrend` 已从旧 `major_trend` proxy 推进到“相对于父趋势参照方向”的诚实语义
2. `wave ledger` 与 `snapshot` 的角色判定已统一
3. `GX4` 完成的是角色判定去伪装，不是三层趋势定义的最终完工
