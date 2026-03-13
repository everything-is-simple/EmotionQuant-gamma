# Phase P5 Sizing Lane Closeout Record

**日期**: `2026-03-14`  
**阶段**: `Positioning / P5`  
**对象**: `第三战场第六张执行卡 formal closeout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P5 / sizing lane closeout / migration boundary` 的正式结论写死。

这张 record 只回答 5 件事：

1. `P0 ~ P4` 合并后，sizing lane 当前到底确认了什么
2. `no retained candidate case` 下，residual watch / watch / no-go 各自是谁
3. 哪些结论只对当前 frozen exit semantics 成立
4. 哪些结论可以压成未来可迁回主线的治理资产
5. `P6 / partial-exit contract freeze` 应以什么前提开工

---

## 2. Formal Inputs

`P5` 只承认以下 formal inputs：

1. `positioning/03-execution/records/01-phase-p0-baseline-freeze-record-20260313.md`
2. `positioning/03-execution/records/02-phase-p1-null-control-matrix-record-20260313.md`
3. `positioning/03-execution/records/03-phase-p2-sizing-family-replay-record-20260314.md`
4. `positioning/03-execution/records/04-phase-p3-single-lot-sanity-replay-record-20260314.md`
5. `positioning/03-execution/records/05-phase-p4-sizing-retained-or-no-go-record-20260314.md`

当前明确不做：

1. `不重跑 sizing replay`
2. `不提前打开 PX1 / cross-exit sensitivity`
3. `不提前打开 partial-exit family replay`

---

## 3. 收官判定

当前 sizing lane 的收官判定固定为：

1. `all_defined_sizing_cards_closed = yes`
2. `all_formal_sizing_records_closed = yes`
3. `retained_sizing_candidate = none`
4. `active_sizing_main_queue = none`
5. `next_main_queue = P6 / partial-exit contract freeze`
6. `future_sizing_reentry_requires = new_sizing_hypothesis_package_or_explicit_migration_package`

这意味着：

`第三战场当前不是“还有 sizing 旧卡没跑完”，而是“已定义的 sizing 主干卡已经全部裁决完毕，当前主队列正式切到 partial-exit lane”。`

---

## 4. Sizing Lane 最终确认了什么

### 4.1 Frozen Baseline 已正式写死

`P0` 已把 sizing lane 的 frozen baseline 固定为：

1. `legacy_bof_baseline`
2. `no IRS`
3. `no MSS`
4. `signal_date = T / execute_date = T+1 / fill = T+1 open`
5. `current Broker full-exit stop-loss + trailing-stop`

同时写死：

`第三战场 sizing lane 不再回答买什么 / 何时买，只回答在固定 baseline 下买多少。`

### 4.2 Control 尺子已正式定下来

`P1` 已正式确认：

1. `FIXED_NOTIONAL_CONTROL = canonical operating control baseline`
2. `SINGLE_LOT_CONTROL = floor sanity control`

这不是主线默认仓位结论，而是：

`后续 Positioning 各 lane 做正式 replay 时必须先拿来当尺子的 control 设计。`

### 4.3 首批 Family 已经跑完并完成裁决

`P2 -> P4` 已把首批 sizing family 跑成最终治理结果：

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 曾在 `P2` 进入 provisional retained 队列
2. 但两者在 `P3 / single-lot sanity replay` 中都没有通过 `sanity_survivor`
3. 因此 `P4` 已正式写定：
   - `retained = []`
   - `residual_watch = [WILLIAMS_FIXED_RISK, FIXED_RATIO]`
   - `watch = [FIXED_RISK, FIXED_VOLATILITY, FIXED_CAPITAL, FIXED_PERCENTAGE]`
   - `no_go = [FIXED_UNIT]`

### 4.4 当前没有任何 sizing formula 可以升格

Sizing lane 当前最关键的正式答案固定为：

1. 当前不存在 `retained sizing candidate`
2. 当前不能把任何 sizing formula 迁回主线当默认仓位
3. `PX1 / cross-exit sensitivity` 继续保持锁住

---

## 5. No-Retained-Candidate Case 最终分层

### 5.1 Residual Watch

当前只保留为 `residual watch` 的对象固定为：

1. `WILLIAMS_FIXED_RISK`
2. `FIXED_RATIO`

它们的含义固定为：

`曾经最接近 retained，但并未通过 sanity survivor。`

### 5.2 Watch

当前保留为 `watch` 的对象固定为：

1. `FIXED_RISK`
2. `FIXED_VOLATILITY`
3. `FIXED_CAPITAL`
4. `FIXED_PERCENTAGE`

它们的含义固定为：

`证据不足以升格，也不足以作为当前主队列重开的对象。`

### 5.3 No-Go

当前正式 `no_go` 的对象固定为：

`FIXED_UNIT`

它的含义固定为：

`已退出 sizing lane 当前主队列。`

---

## 6. 哪些结论只对当前 Frozen Exit Semantics 成立

当前明确只对以下 frozen 口径成立：

1. `no retained sizing candidate` 这一定论，只在 `current Broker full-exit stop-loss + trailing-stop` 下被正式证明
2. `WILLIAMS_FIXED_RISK / FIXED_RATIO = residual watch` 的身份，只在当前 full-exit 语义下成立，尚未通过 `PX1`
3. `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE = watch` 的排序位置，也只对当前 exit baseline 成立
4. `FIXED_UNIT = no_go` 当前不重审，也不外推成“跨所有 exit family 永久无效”

一句话说：

`本轮 sizing 结论已经足够收口当前 lane，但它们还不是跨 exit baseline 的普适真理。`

---

## 7. 哪些结论可以沉淀成治理资产

当前可以沉淀并迁移的，不是新的 sizing 默认参数，而是治理边界：

1. `先 freeze baseline，再跑 family replay`
2. `canonical operating control` 与 `floor sanity control` 必须分开定义
3. `provisional retained != retained`
4. `single-lot sanity` 是 retained promotion 前的必要门槛之一
5. `residual watch != retained candidate`
6. `no retained sizing candidate => PX1 继续锁住`
7. `partial-exit lane` 不得拿 sizing lane 的 residual watch 当作隐含 baseline

一句话说：

`可迁回主线和后续 lane 的，是治理约束与负面边界，不是新的仓位公式。`

---

## 8. P6 Opening Boundary

`P6 / partial-exit contract freeze` 的 opening boundary 固定为：

1. `entry baseline 不变`
2. `sizing baseline = P5 closeout baseline`
3. `P5 closeout baseline` 当前具体写定为：
   - `FIXED_NOTIONAL_CONTROL = operating control baseline`
   - `SINGLE_LOT_CONTROL = floor sanity baseline`
4. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 不作为 `P6` 输入 baseline
5. `watch / residual watch / no_go` 全部不得在 `P6` 被偷渡成 partial-exit family 前提
6. `P6` 只冻结契约、状态机、trace 与兼容边界，不比较 exit family 优劣

---

## 9. 正式结论

当前 `P5 sizing lane closeout` 的正式结论固定为：

1. 第三战场 sizing lane 当前已经完成收官
2. sizing lane 当前正式确认：
   - frozen baseline 已锁定
   - control 尺子已锁定
   - 首批 family 已完成 retained-or-no-go 裁决
3. 当前 `retained sizing candidate = []`
4. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 只保留为 residual watch
5. `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE` 继续保留为 watch
6. `FIXED_UNIT` 维持 `no_go`
7. 当前可迁移的是治理资产与负面约束，不是新的主线默认仓位
8. 第三战场主队列正式切到 `P6 / partial-exit contract freeze`

---

## 10. 一句话结论

`P5` 已把 sizing lane 正式收官：该冻结的已经冻结，该观察的留档观察，该否决的已经否决；现在能带去下一段的是治理边界，不是新的默认仓位公式。
