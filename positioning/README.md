# Positioning

**状态**: `Active`  
**日期**: `2026-03-15`

---

## 1. 定位

`positioning/` 是 `EmotionQuant-gamma` 根目录下的第三战场设计空间，也是当前仓库专门面向“买多少 / 卖多少”的独立研究线。

它的职责只有一个：

`在不依赖 MSS / IRS 的前提下，独立验证账户该怎么活、怎么长。`

这里不是 `blueprint/` 的替代品，也不是对 `Normandy` 已收官卡片的续跑。

这里还必须再写死一条：

`Positioning 不是 v0.01 的子版本号，也不是新的主线版本线。`

它是研究战场，不是版本线。

---

## 2. 和当前主线 / Normandy 的边界

当前仓库已经有两块已知前提：

1. `blueprint/` + `docs/spec/v0.01-plus/` 代表当前主线
2. `normandy/` 已完成 `alpha provenance + quality gate + exit damage diagnosis`

因此 `positioning/` 的边界固定为：

1. 不重开 `买什么 / 何时买` 的 alpha provenance 问题
2. 不继续在 `Normandy` 里续跑旧卡
3. 不让 `MSS / IRS` 进入仓位决定
4. 先在固定 baseline 下回答 `买多少`
5. 再在补齐 `Broker` 的部分减仓契约后回答 `卖多少`
6. 若研究结论未来需要升格，必须先形成正式 record，再迁回 `blueprint/`

---

## 3. 分层结构

`positioning/` 固定沿用 `blueprint/` 的三层结构：

1. `01-full-design/`
   - 第三战场完整设计 SoT
   - 当前尚未展开正文
2. `02-implementation-spec/`
   - 从完整设计中裁出的当前实验实现方案
   - 只定义本轮仓位研究范围和冻结口径
3. `03-execution/`
   - phase / task / checklists / evidence contract
   - 只服务执行，不承担算法正文

---

## 4. 当前目标

第三战场的当前目标固定为两段：

1. 先在固定 `legacy_bof_baseline / no IRS / no MSS` 前提下，独立验证 `position sizing`
2. 再在 `Broker` 明确支持 `partial-exit / scale-out` 后，独立验证 `卖多少`

当前首批 sizing hypothesis register 固定为：

1. `single-lot control`
2. `fixed-notional control`
3. `fixed-risk`
4. `fixed-capital`
5. `fixed-ratio`
6. `fixed-unit`
7. `williams-fixed-risk`
8. `fixed-percentage`
9. `fixed-volatility`

当前一句话目标可以压成：

`先把仓位和 MSS / IRS 解绑，再在固定 BOF baseline 下把“买多少 / 卖多少”单独跑成证据链。`

---

## 5. 当前入口

当前已经落下的入口文件有：

- `../docs/spec/common/records/repo-line-map-20260312.md`
- `02-implementation-spec/01-positioning-baseline-and-sizing-spec-20260313.md`
- `02-implementation-spec/02-partial-exit-contract-spec-20260314.md`
- `03-execution/01-phase-p0-baseline-freeze-card-20260313.md`
- `03-execution/records/01-phase-p0-baseline-freeze-record-20260313.md`
- `03-execution/02-phase-p1-null-control-matrix-card-20260313.md`
- `03-execution/records/02-phase-p1-null-control-matrix-record-20260313.md`
- `03-execution/03-phase-p2-sizing-family-replay-card-20260313.md`
- `03-execution/04-phase-p3-single-lot-sanity-replay-card-20260314.md`
- `03-execution/records/04-phase-p3-single-lot-sanity-replay-record-20260314.md`
- `03-execution/05-phase-p4-sizing-retained-or-no-go-card-20260314.md`
- `03-execution/records/05-phase-p4-sizing-retained-or-no-go-record-20260314.md`
- `03-execution/06-phase-p5-sizing-lane-closeout-migration-boundary-card-20260314.md`
- `03-execution/records/06-phase-p5-sizing-lane-closeout-record-20260314.md`
- `03-execution/records/sizing-lane-migration-boundary-table-20260314.md`
- `03-execution/records/partial-exit-lane-opening-note-20260314.md`
- `03-execution/07-phase-p6-partial-exit-contract-freeze-card-20260314.md`
- `03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
- `03-execution/records/partial-exit-control-definition-note-20260314.md`
- `03-execution/08-phase-p7-partial-exit-null-control-matrix-card-20260314.md`
- `03-execution/09-phase-p8-partial-exit-family-replay-card-20260314.md`
- `03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
- `03-execution/10-phase-p9-positioning-campaign-closeout-card-20260314.md`
- `03-execution/11-phase-px1-cross-exit-sensitivity-card-20260314.md`
- `03-execution/12-phase-px2-targeted-mechanism-follow-up-card-20260314.md`

它们分别负责：

1. 仓库层面的历史线 / 主线 / 研究线总拓扑说明
2. 第三战场当前唯一实现方案：先冻结 baseline，再逐类验证 sizing
3. `P6` partial-exit 契约 spec：把多腿 SELL、状态机、report 和兼容边界正式写死
4. 第三战场第一张执行卡：把对照组、继承口径和禁止混问写死
5. `P0` 首轮 formal readout：把 frozen baseline、control 组、首批 sizing register 和下一张执行卡正式写死
6. `P1` formal readout：把 `single-lot control / fixed-notional control` 跑成正式 null control matrix，并把 `FIXED_NOTIONAL_CONTROL` 写定为 canonical control baseline
7. `P2` formal readout：首批 sizing family 已跑出 provisional retained candidate，并已把 `WILLIAMS_FIXED_RISK / FIXED_RATIO` 推进到下一张卡
8. `P3` formal readout：`WILLIAMS_FIXED_RISK / FIXED_RATIO` 拉回 `SINGLE_LOT_CONTROL` 后都没有通过 `sanity_survivor` 门槛，当前正式结论已固定为 `no_candidate_survives_single_lot_sanity`
9. `P4` formal readout：第三战场 sizing lane 已被正式裁成 `no retained candidate case`
10. `P5` formal closeout：已把 sizing lane 收口成 `closeout record + migration boundary table + partial-exit opening note`
11. `P6` formal freeze：已把 partial-exit lane 的 contract、状态机和 control baseline 正式写死
12. `P7` formal readout：`FULL_EXIT_CONTROL` 保持 partial-exit lane 的 canonical control baseline，naive 50/50 scale-out 只保留为 operating-side 局部改善
13. `P8` formal readout：首批 partial-exit family 已跑出 retained queue，当前 provisional leader = `TRAIL_SCALE_OUT_25_75`
14. `P9` 当前 active card：把第三战场收官排成后续主干卡
15. `PX1 / PX2`：只在触发条件满足时打开的条件卡，`PX2` 仅在显式 targeted mechanism hypothesis 下允许打开

---

## 5.1 当前全卡序列

第三战场当前已经把后续全卡序列明确为：

1. `P0 baseline freeze`
2. `P1 null control matrix`
3. `P2 sizing family replay`
4. `P3 single-lot sanity replay`
5. `P4 sizing retained-or-no-go`
6. `P5 sizing lane closeout / migration boundary`
7. `P6 partial-exit contract freeze`
8. `P7 partial-exit null control matrix`
9. `P8 partial-exit family replay`
10. `P9 positioning campaign closeout`
11. `PX1 cross-exit sensitivity`（条件卡）
12. `PX2 targeted mechanism follow-up`（条件卡）

当前治理规则固定为：

1. `P9` 是唯一 active card
2. `PX1` 继续保持 locked，未被 `P8` 自动打开
3. `PX2` 只有在显式 targeted mechanism hypothesis 满足后才允许打开

---

## 6. 使用规则

1. 先看 `docs/spec/common/records/repo-line-map-20260312.md`，确认当前自己站在主线还是研究线
2. 再看 `blueprint/README.md`，确认当前默认运行口径仍是 `legacy_bof_baseline`
3. 再看 `normandy/README.md`，确认 `买什么 / 何时买 / 是否卖坏` 已由第二战场处理
4. 再看 `positioning/02-implementation-spec/`，确认当前实验允许做什么、不允许做什么
5. 最后才看当前 phase card

---

## 7. 当前一句话基线

第三战场当前一句话基线固定为：

`Positioning 是研究线，不是版本线；先解买多少，再解卖多少；不让 MSS / IRS 参与仓位决定。`
