# GX6 Evidence: 1-2-3 三条件语义整改验证

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 证据来源

1. 配套 record：`records/17-phase-gx6-123-three-condition-refactor-record-20260318.md`
2. 本文件只整理 record 中已固化的条件映射、字段与验证结果

---

## 2. 三条件映射证据

1. `123_STEP1 -> trendline_break`
2. `123_STEP2 -> failed_extreme_test`
3. `123_STEP3 -> prior_pivot_breach`
4. `turn_confirm_type` 现在只在三条件齐备时写出：
   - `CONFIRMED_TURN_UP`
   - `CONFIRMED_TURN_DOWN`

---

## 3. 落盘字段证据

1. `l3_gene_wave.turn_step1_condition`
2. `l3_gene_wave.turn_step2_condition`
3. `l3_gene_wave.turn_step3_condition`
4. `l3_gene_event.structure_condition`
5. `schema version = v14`

---

## 4. 验证命令证据

1. `python -m pytest tests/unit/selector/test_gene.py -q`
   - `4 passed`
2. `python -m py_compile src/selector/gene.py src/data/store.py tests/unit/selector/test_gene.py`
   - `通过`

---

## 5. Evidence verdict

当前证据支持：

1. `1-2-3` 已从结果标签推进成可审计的三条件确认语法
2. `wave / event` 两层已能回看每一步条件，而不只剩最终 turn 结论
3. `GX6` 完成的是条件拆账，不是 trendline 理论的全对象化终局版
