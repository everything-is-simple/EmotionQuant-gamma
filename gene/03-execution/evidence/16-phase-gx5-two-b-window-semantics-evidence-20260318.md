# GX5 Evidence: 2B 时间窗语义整改验证

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 证据来源

1. 配套 record：`records/16-phase-gx5-two-b-window-semantics-record-20260318.md`
2. 本文件只整理 record 中已固化的窗口 spec、字段与验证结果

---

## 2. 时间窗语义证据

1. 旧固定口径 `TWO_B_CONFIRMATION_BARS = 3` 已移除
2. 新层级窗口 spec 固定为：
   - `SHORT -> 1 bar`
   - `INTERMEDIATE -> 3-5 bar`
   - `LONG -> 7-10 bar`
3. 当前 active 检测上界写成：
   - `SHORT -> 1`
   - `INTERMEDIATE -> 5`
   - `LONG -> 10`
4. 当前正式 basis 文案包括：
   - `SHORT_WITHIN_1_BAR`
   - `INTERMEDIATE_WITHIN_3_TO_5_BARS`
   - `LONG_WITHIN_7_TO_10_BARS`

---

## 3. 落盘字段证据

1. `l3_gene_event.confirmation_window_bars`
2. `l3_gene_event.confirmation_window_basis`
3. `l3_gene_wave.two_b_window_bars`
4. `l3_gene_wave.two_b_window_basis`
5. `l3_stock_gene.current_two_b_window_bars`
6. `l3_stock_gene.current_two_b_window_basis`
7. `schema version = v13`

---

## 4. 验证命令证据

1. `python -m pytest tests/unit/selector/test_gene.py -q`
   - `4 passed`
2. `python -m py_compile src/selector/gene.py src/data/store.py tests/unit/selector/test_gene.py`
   - `通过`

---

## 5. Evidence verdict

当前证据支持：

1. `2B` 已从固定 magic number 改成层级相关确认窗
2. 当前 active 语义已诚实写成 `INTERMEDIATE 3-5 bar`
3. 下游已能看到 `2B` 的窗口 bars 与 basis，不再只有事件名
