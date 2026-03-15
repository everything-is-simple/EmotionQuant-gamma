# Phase N3d EmotionQuant Module Reuse Triage Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3d`  
**对象**: `EmotionQuant-gamma 对立花验证可复用资产正式分流`  
**状态**: `Closed`

---

## 1. 目标

本卡只回答 4 件事：

1. `EmotionQuant-gamma` 里哪些模块可以直接承接立花验证  
2. 哪些模块只能改造后复用  
3. 哪些旧模块应退出立花主线  
4. 后续立花实现应从哪条工程主干推进

---

## 2. Formal Inputs

本卡正式输入固定为：

1. `src/contracts.py`
2. `src/broker/broker.py`
3. `src/backtest/engine.py`
4. `src/backtest/partial_exit_null_control.py`
5. `src/backtest/positioning_partial_exit_family.py`
6. `src/backtest/normandy_tachibana_alpha.py`
7. `src/strategy/tachibana_detectors.py`
8. `src/report/reporter.py`
9. `tests/unit/broker/test_broker.py`
10. `tests/patches/broker/test_broker_trace_semantics_regression.py`
11. `scripts/backtest/run_positioning_*.py`
12. `scripts/backtest/run_normandy_tachibana_alpha_*.py`
13. `normandy/02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md`
14. `normandy/02-implementation-spec/10-tachibana-quantifiable-execution-system-spec-20260315.md`
15. `normandy/03-execution/evidence/tachibana_execution_semantics_evidence_table_20260315.md`
16. `normandy/03-execution/evidence/tachibana_replay_ledger_contract_note_20260315.md`
17. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
18. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`

---

## 3. 正式裁决

当前正式裁决固定为：

1. `positioning + partial_exit + contracts + reporter + broker trace tests` 升格为立花验证可直接复用主干  
2. `broker / engine / old tachibana alpha` 保留为改造后复用资产，不得直接冒充立花原书执行器  
3. `run_normandy_tachibana_alpha_*` 与 `05-tachibana-contrary-alpha-search-spec-20260312.md` 退出立花主线  
4. 当前立花工程主线固定为：  
   `tradebook scaffold -> replay ledger -> state transition rules -> positioning validation`

---

## 4. 关键理由

### 4.1 为什么直接复用主干不是旧 tachibana alpha

因为旧 `tachibana alpha` 只回答：

`有没有一类反人群失败回收形态能单独跑出 edge`

而当前立花问题真正要回答的是：

`如何通过试单、母单、离散加减仓、锁单、休息，把机会管理成部位路径`

这两者不是一个问题。

### 4.2 为什么 partial-exit/positioning 是当前最值钱的

因为仓库里已经有：

1. `position-aware identity`
2. `multi-leg exit contract`
3. `family replay`
4. `retained / watch / control baseline` 的实验治理能力

这正是把书中执行法转成可验证系统时最难补的一层。

### 4.3 为什么 Broker 只能算改造后复用

因为当前主线仍然是：

1. `Signal BUY-only`
2. `Broker` 围绕 A 股长仓入场和退出运作
3. 原书里的 `long-short lock coexistence` 不能直接原样装入当前执行内核

所以 Broker 当前更适合承接：

`立花方法中能迁回 A 股 BOF 主线的部分`

而不是整本书的原始交易宇宙。

---

## 5. 产出物

本卡的正式产出固定为：

`normandy/03-execution/evidence/emotionquant_tachibana_module_reuse_triage_table_20260315.md`

---

## 6. 下一张卡

本卡完成后的 next main queue card 固定为：

`N3e / Tachibana state-transition candidate table`

它只允许回答：

1. 书中哪些动作属于 `试单`
2. 哪些动作属于 `母单扩张`
3. 哪些动作属于 `锁单测试`
4. 哪些动作属于 `解锁 / 反向 / 全平休息`
5. 哪些动作可以映射到当前 `position_id / exit_leg_id / partial_exit family`

---

## 7. 一句话结论

`EmotionQuant-gamma` 对立花最有用的不是旧 detector，而是已经成熟的 position-aware execution research stack；后续应沿这条主干推进，而不是回到 contrary alpha 的旧入口。
