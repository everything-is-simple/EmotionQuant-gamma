# G3 Evidence: 结构标签校准主库读数

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 证据来源

1. 配套 record：`records/06-phase-g3-structure-label-calibration-record-20260316.md`
2. 主库：`G:\EmotionQuant_data\emotionquant.duckdb`
3. 截至日：`2026-02-24`
4. 本文件只整理 record 中已固化的结构标签分布与快照读数

---

## 2. 写入规模

1. `_meta_schema_version = 7`
2. `compute_gene()` 本轮真实写入：`2,207,533` 行

---

## 3. `l3_gene_wave` 结构标签分布

1. `turn_confirm_type`
   - `CONFIRMED_TURN_UP = 52,905`
   - `CONFIRMED_TURN_DOWN = 39,561`
2. `two_b_confirm_type`
   - `2B_TOP = 38,980`
   - `2B_BOTTOM = 15,508`

---

## 4. `l3_gene_event` 结构事件分布

1. `123_STEP1 / UP = 52,905`
2. `123_STEP2 / UP = 52,905`
3. `123_STEP3 / UP = 52,905`
4. `123_STEP1 / DOWN = 39,561`
5. `123_STEP2 / DOWN = 39,561`
6. `123_STEP3 / DOWN = 39,561`
7. `2B_TOP / DOWN = 53,195`
8. `2B_BOTTOM / UP = 22,799`

---

## 5. 当日快照证据

`2026-02-24`：

1. `latest_confirmed_turn_type`
   - `CONFIRMED_TURN_UP = 3,149`
   - `CONFIRMED_TURN_DOWN = 2,310`
   - `NONE = 15`
2. `latest_two_b_confirm_type`
   - `2B_TOP = 4,433`
   - `2B_BOTTOM = 1,027`
   - `NONE = 14`

---

## 6. Evidence verdict

当前证据支持：

1. `1-2-3` 已从粗 `reversal_tag` 升级为正式结构标签
2. `2B` 已从布尔失败标记升级为正式事件类型
3. `wave / event / snapshot` 三层已共享同一套结构字段
4. 现有 record 没有出现足以触发 `GX1` 的阻塞级一致性故障证据
