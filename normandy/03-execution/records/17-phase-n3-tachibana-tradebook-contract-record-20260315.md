# Phase N3 Tachibana Tradebook Contract Record

**日期**：`2026-03-15`  
**状态**：`Closed`

本阶段完成了 `Track T0` 的第一步：把 `Pioneer 1975-1976 交易谱` 从“资料集合”收成了“抽取契约 + 结构化骨架”。

本轮确认了三个关键事实：

1. `xlsx` 可以稳定提供日期和收盘价骨架
2. `xlsx` 的交易与未平仓标记并不是机器可读单元格值
3. 第一轮正确做法是先建立 `ledger scaffold`，再逐月人工回填交易动作

本轮新增产物：

1. `scripts/ops/build_tachibana_tradebook_scaffold.py`
2. `normandy/03-execution/evidence/tachibana_tradebook_contract_note_20260315.md`
3. `normandy/03-execution/evidence/tachibana_tradebook_ledger_scaffold_1975_1976.csv`
4. `normandy/03-execution/evidence/tachibana_tradebook_scaffold_digest_20260315.json`

当前结论不是“交易谱已经读出来了”，而是：

`交易谱的价格日历骨架已经固定，下一步应进入逐月交易动作回填。`
