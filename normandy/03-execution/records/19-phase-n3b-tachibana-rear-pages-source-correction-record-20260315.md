# Phase N3b Tachibana Rear Pages Source Correction Record

**日期**：`2026-03-15`  
**状态**：`Closed`

本阶段修正了 `Track T0` 的事实源。

本轮结论：

1. `丽花义正-交易谱（1975.01-1976.12）` 目录中的月度 pdf 是用户自用表框，不是原始交易事实页
2. `B0289-B0302` 才是当前真正可抽取的月度交易表
3. 这些后页表格显示立花使用的是 `买/卖` 双栏和 `未平仓(多/空)` 双栏

这条修正非常关键，因为它直接改变了数据契约：

1. 不再把 `open_units` 当作单值
2. 正式承认 `open_long_units` 与 `open_short_units` 需要并存

本轮新增产物：

1. `normandy/03-execution/evidence/tachibana_book_rear_pages_source_note_20260315.md`
2. `normandy/03-execution/evidence/tachibana_book_monthly_tables_1976_02_1976_12_event_extract_20260315.csv`

当前结论：

`立花方法的执行语义必须允许锁单共存，这不是附带细节，而是原始表结构本身。`
