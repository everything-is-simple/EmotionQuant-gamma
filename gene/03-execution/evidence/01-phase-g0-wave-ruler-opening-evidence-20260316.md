# G0 Evidence: 历史波段标尺脚手架主库验收

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 证据来源

1. 配套 record：`records/01-phase-g0-wave-ruler-opening-record-20260316.md`
2. 主库：`G:\EmotionQuant_data\emotionquant.duckdb`
3. 本文件只整理 record 中已固化的验收读数，不新增未出现在 record 的结论

---

## 2. 运行验收口径

1. 命令：`python main.py build --layers l3 --end 2026-02-24`
2. 运行元数据：`build_dtt_v0_01_dtt_pattern_plus_irs_score_n20260316_t015528`
3. 结果：`SUCCESS`
4. `schema version = v5`

---

## 3. 主库落表证据

1. `l3_stock_gene`
   - `4,030,427` 行
   - 日期范围：`2023-01-03 -> 2026-02-24`
2. `l3_gene_wave`
   - `871,174` 行
   - 日期范围：`2023-01-05 -> 2026-02-11`
3. `l3_gene_event`
   - `216,062` 行
   - 日期范围：`2023-01-04 -> 2026-02-11`

---

## 4. 实现口径证据

1. 价格来源固定为 `l2_stock_adj_daily`
2. `pivot` 使用第一版 `5-bar confirmation scaffold`
3. `wave` 由相邻反向 `pivot` 组成
4. `event` 由新高/新低刷新与 `2B` 失败检测形成
5. `snapshot` 同时输出自历史与横截面两套标尺

---

## 5. Evidence verdict

当前证据支持：

1. 第四战场对象层已进入主库并完成第一次真实回填
2. `l3_stock_gene / l3_gene_wave / l3_gene_event` 三张正式表合同已落下
3. `G0` 可以按“脚手架已完成并可承接 `G1`”收口
