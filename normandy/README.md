# Normandy

**状态**: `Active`  
**日期**: `2026-03-12`

---

## 1. 定位

`normandy/` 是 `EmotionQuant-gamma` 根目录下的第二战场设计空间，也是当前仓库唯一独立研究线。

它的职责只有一个：

`隔离“alpha 来源证明 + exit 伤害拆解”这条新实验主线。`

这里不是 `blueprint/` 的替代品，也不是对当前 `v0.01-plus` 主线的口头修修补补。

这里还必须再写死一条：

`Normandy 不是 v0.01 的子版本号，也不是新的主线版本线。`

它是研究战场，不是版本线。

---

## 2. 和当前主线的边界

当前仓库已经有一条正式主线：

1. `blueprint/`
2. `docs/spec/v0.01-plus/`
3. `docs/spec/common/records/development-status.md`

这条主线已经完成：

1. `Phase 0`
2. `Phase 1`
3. `Phase 1.5`
4. `Phase 2`
5. `Phase 3`
6. `Phase 4 / Gate`
7. `Phase 4.1 / MSS-Broker Remediation`

并且当前裁决已经固定为：

`v0.01-plus` 默认路径未通过 `Phase 4 Gate`，当前默认运行口径继续保持 `legacy_bof_baseline`。

因此 `normandy/` 的角色固定为：

1. 不改写 `Phase 3 completed` 的结论。
2. 不改写 `Phase 4 / Gate = NO-GO` 的结论。
3. 不继续沿 `Phase 4.1` 做 `MSS / Broker` 微调。
4. 单独回答“真实 alpha 来自哪里，收益是被谁吞掉”的问题。
5. 若研究结论未来需要升格，必须先形成正式 record，再迁回 `blueprint/`，不能靠 `normandy/` 直接宣布主线改写。

---

## 3. 分层结构

`normandy/` 固定沿用 `blueprint/` 的三层结构：

1. `01-full-design/`
   - 第二战场完整设计 SoT
   - 只回答研究边界和系统性问题

2. `02-implementation-spec/`
   - 从完整设计中裁出的当前实验实现方案
   - 只定义本轮实验范围和对照口径

3. `03-execution/`
   - phase / task / checklists / evidence contract
   - 只服务执行，不承担算法正文

---

## 4. 当前目标

第二战场的当前目标固定为三件事：

1. 先证明 `PAS raw alpha` 到底来自哪类 entry。
2. 再在 `BOF / pinbar` family 内部，用同一套 Broker 出场语义做 quality split。
3. 最后才拆 `exit damage`，确认问题是在“买错”还是“卖坏”。

一句话说：

`Normandy 不是为了继续救当前 plus 默认路径，而是为了先把 alpha 来源、BOF family quality 和 exit / execution 伤害拆干净。`

---

## 5. 当前入口

当前已经落下的入口文件有：

- `../docs/spec/common/records/repo-line-map-20260312.md`
- `01-full-design/01-alpha-first-mainline-charter-20260312.md`
- `01-full-design/README.md`
- `90-archive/README.md`
- `01-full-design/90-research-assets/bof-pinbar-keylevel-doctrine-note-20260312.md`
- `02-implementation-spec/01-alpha-provenance-and-exit-decomposition-spec-20260311.md`
- `02-implementation-spec/02-volman-second-alpha-search-spec-20260312.md`
- `02-implementation-spec/03-fb-second-layer-provenance-spec-20260312.md`
- `02-implementation-spec/04-fb-stability-and-purity-spec-20260312.md`
- `02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md`
- `02-implementation-spec/06-fb-detector-refinement-spec-20260312.md`
- `02-implementation-spec/07-fb-boundary-stability-follow-up-spec-20260312.md`
- `02-implementation-spec/08-sb-refinement-or-no-go-spec-20260312.md`
- `02-implementation-spec/09-bof-pinbar-broker-frozen-go-spec-20260312.md`
- `01-full-design/90-research-assets/README.md`
- `01-full-design/90-research-assets/tachibana-crowd-failure-minimal-contract-note-20260312.md`
- `03-execution/00-dev-data-baseline-inheritance-20260311.md`
- `03-execution/01-phase-n1-pas-alpha-provenance-card-20260311.md`
- `03-execution/02-phase-n1-5-volman-second-alpha-card-20260312.md`
- `03-execution/03-phase-n1-6-fb-second-layer-provenance-card-20260312.md`
- `03-execution/04-phase-n1-7-fb-stability-and-purity-card-20260312.md`
- `03-execution/05-phase-n1-8-tachibana-contrary-alpha-card-20260312.md`
- `03-execution/06-phase-n1-9-fb-detector-refinement-card-20260312.md`
- `03-execution/07-phase-n1-9a-fb-boundary-stability-follow-up-card-20260312.md`
- `03-execution/08-phase-n1-10-sb-refinement-or-no-go-card-20260312.md`
- `03-execution/09-phase-n1-11-bof-pinbar-quality-provenance-card-20260312.md`
- `03-execution/10-phase-n1-12-bof-pinbar-stability-or-no-go-card-20260312.md`
- `03-execution/records/05-phase-n1-7-fb-stability-and-purity-record-20260312.md`
- `03-execution/records/04-phase-n1-8-tachibana-contrary-alpha-record-20260312.md`
- `03-execution/records/06-phase-n1-9-fb-detector-refinement-record-20260312.md`
- `03-execution/records/07-phase-n1-9a-fb-boundary-stability-follow-up-record-20260312.md`
- `03-execution/records/08-phase-n1-10-sb-refinement-or-no-go-record-20260312.md`
- `03-execution/records/00-normandy-interim-conclusions-20260312.md`

它们分别负责：

1. 仓库层面的历史线 / 主线 / 研究线三分地图。
2. 第二战场已经激活的 full-design 总纲：把 `alpha-first` 主线、模块职责、对象裁决和升格法正式写死。
3. 第二战场完整设计层的统一入口。
4. 研究线早期方案和已退场计划的归档层。
5. `BOF / pinbar / key-level` 交集语义的战役专用来源归纳。
6. 第二战场当前实验范围与对照约束。
7. 在 `BOF` baseline 固定后，单独搜索第二个自带 alpha 的 `Volman` 候选。
8. 在 `FB` 已成为第二个 alpha 候选后，继续做第二层 provenance。
9. 在 `FB` 已通过第二层 dossier 后，继续做稳定性与 purity 审核。
10. 在 `N1.7` 已固定 “boundary-loaded” 后，把 `FB` 正式拆成 `cleaner` 与 `boundary` 两支。
11. 在 retained branch 已经固定后，再对 `FB_BOUNDARY` 做 focused stability follow-up。
12. 围绕 `SB` 做 refinement / no-go formal readout，并固定 full detector 与窄 watch branch 的去留。
13. `BOF family` 当前新的 broker-frozen go path：在无 `MSS / IRS` 的前提下，只围绕 `key-level / pinbar` 做 quality split。
14. `Normandy` 专属 research asset 的统一入口。
15. 基于 `Tachibana` 理论骨架，把 `TACHI_CROWD_FAILURE` 收缩成最小 formal contract。
16. 三目录纪律、执行库 / 旧库候选、`RAW_DB_PATH`、双 TuShare key 的继承规则。
17. 第一张执行卡：先做 `PAS raw alpha provenance`。
18. 第二张执行卡：围绕 `RB_FAKE / SB / FB` 搜索第二个自带 alpha 候选。
19. 第三张执行卡：围绕 `FB` 做 focused dossier，判断它是稳定补充型 alpha，还是暂时成立的小样本候选。
20. 第四张执行卡：围绕 `FB` 做 stability / purity 审核，并明确是否进入 `N2`。
21. `N1.7` 首轮 formal readout：固定 `FB` 当前仍是第二 alpha 候选，但下一步必须先做 detector refinement，而不是直接进入 `N2`。
22. 第五张执行卡：围绕 `Tachibana contrary alpha` 做第一轮 formal backtest screen。
23. 第六张执行卡：把 `FB` 正式拆成 `FB_CLEANER / FB_BOUNDARY` 做 refinement matrix。
24. 第七张执行卡：围绕 retained branch `FB_BOUNDARY` 做 focused stability follow-up。
25. 第八张执行卡：围绕 `SB` 做 refinement / no-go formal readout。
26. 第九张执行卡：围绕 `BOF` quality branches 做 provenance readout。
27. 第十张执行卡：围绕 retained `BOF` branch 做 stability / no-go formal readout。
28. `N1.8` 首轮 formal readout：固定 `TACHI_CROWD_FAILURE` 当前只是 observation-only，而不是独立 alpha 胜者。
29. `N1.9` 首轮 formal readout：固定 `FB_BOUNDARY` 是当前 retained branch，但它仍需先做 stability follow-up，不能直接打开 `N2`。
30. `N1.9A` 首轮 formal readout：固定 `FB_BOUNDARY` 当前仍不够稳，主队列优先级切到 `SB refinement or no-go`。
31. `N1.10` 首轮 formal readout：固定 `SB` 当前 full detector 路线 `no-go`，但保留 `SB_SMALL_W_MID_STRENGTH` 为窄 watch branch，并把主队列切到 `Tachibana detector refinement or backlog retention`。
32. 当前阶段性结论、对象分层与延后研究清单。

---

## 6. 使用规则

1. 先看 `docs/spec/common/records/repo-line-map-20260312.md`，确认当前自己站在历史线、主线还是研究线。
2. 再看 `blueprint/README.md`，确认当前主线已经冻结到哪里。
3. 再看 `normandy/README.md`，确认第二战场的问题边界。
4. 再看 `02-implementation-spec/`，确认本轮实验允许做什么、不允许做什么。
5. 再看 `03-execution/00-dev-data-baseline-inheritance-20260311.md`，确认三目录纪律、执行库与双 TuShare key 口径。
6. 最后才看当前 phase card。

---

## 7. 当前一句话基线

第二战场当前一句话基线固定为：

`保持 blueprint 主线结论不变，以 legacy_bof_baseline 为当前默认运行口径，在继承同一套三目录 / 执行库 / 旧库 / TuShare 双通道纪律的前提下，先独立证明 PAS raw alpha，再在同一套 Broker 下把 BOF family quality 读干净，最后才拆 exit damage。`

再压缩一句：

`Normandy 是研究线，不是版本线；它负责找答案，不负责直接改写主线。`
