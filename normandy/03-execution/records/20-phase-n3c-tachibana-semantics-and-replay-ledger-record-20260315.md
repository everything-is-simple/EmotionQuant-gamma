# Phase N3c Tachibana Semantics And Replay Ledger Record

**日期**：`2026-03-15`  
**状态**：`Closed`

本阶段同时完成了两条工作：

1. `B0288-B0305` 的执行语义证据表
2. 基于 `74` 条事件的正式回放台账

本轮关键成果：

1. 方法页已经足以固定立花 doctrine 的最小骨架：
   `分批交易 / 锁单作为测试机制 / 母单维持 / 小张数 / 全平休息`
2. 回放台账已经能明确识别：
   `enter / add / cover / reverse / lock / unlock`
3. 立花方法当前最重要的形式化突破是：
   `未平仓不能再写成单值，必须拆成 long/short 双侧状态`

本轮新增产物：

1. `normandy/03-execution/evidence/tachibana_execution_semantics_evidence_table_20260315.md`
2. `normandy/03-execution/evidence/tachibana_replay_ledger_contract_note_20260315.md`
3. `normandy/03-execution/evidence/tachibana_replay_ledger_1976_02_1976_12_20260315.csv`
4. `scripts/ops/build_tachibana_replay_ledger.py`

当前结论：

`立花方法已经不再只是一本书里的描述，而是可以被回放为带 position_id / leg_id / state_transition 的执行状态机。`
