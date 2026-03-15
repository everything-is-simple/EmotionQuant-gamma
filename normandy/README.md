# Normandy

**状态**: `Active`  
**日期**: `2026-03-15`

---

## 1. 定位

`normandy/` 是 `EmotionQuant-gamma` 根目录下的第二战场设计空间，也是当前仓库的一条独立研究线。

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

第二战场的当前目标固定为四件事：

1. 先证明 `PAS raw alpha` 到底来自哪类 entry。
2. 再在 `BOF / pinbar` family 内部，用同一套 Broker 出场语义做 quality split。
3. 最后才拆 `exit damage`，确认问题是在“买错”还是“卖坏”。
4. 在不伪装“完整复刻立花系统”的前提下，把 `Tachibana` 收成可回放、可迁移的 execution subset。

一句话说：

`Normandy 不是为了继续救当前 plus 默认路径，而是为了先把 alpha 来源、BOF family quality、exit / execution 伤害，以及 Tachibana 可迁移执行子集拆干净。`

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
- `02-implementation-spec/10-tachibana-quantifiable-execution-system-spec-20260315.md`
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
- `03-execution/11-phase-n1-13-tachibana-refinement-or-backlog-retention-card-20260313.md`
- `03-execution/12-phase-n2-bof-control-baseline-exit-decomposition-card-20260313.md`
- `03-execution/13-phase-n2a-targeted-trailing-stop-follow-up-card-20260313.md`
- `03-execution/17-phase-n3-tachibana-tradebook-contract-card-20260315.md`
- `03-execution/18-phase-n3a-tachibana-january-sample-blocker-card-20260315.md`
- `03-execution/19-phase-n3b-tachibana-rear-pages-source-correction-card-20260315.md`
- `03-execution/20-phase-n3c-tachibana-semantics-and-replay-ledger-card-20260315.md`
- `03-execution/21-phase-n3d-emotionquant-module-reuse-triage-card-20260315.md`
- `03-execution/22-phase-n3e-tachibana-state-transition-candidate-table-card-20260315.md`
- `03-execution/23-phase-n3f-tachibana-validation-rule-candidate-matrix-card-20260315.md`
- `03-execution/24-phase-n3g-tachibana-pilot-pack-opening-note-card-20260315.md`
- `03-execution/25-phase-n3h-tachibana-pilot-pack-executable-matrix-card-20260315.md`
- `03-execution/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-card-20260315.md`
- `03-execution/27-phase-n3j-tachibana-pilot-pack-runner-implementation-card-20260315.md`
- `03-execution/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-card-20260315.md`
- `03-execution/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-card-20260315.md`
- `03-execution/30-phase-n3m-tachibana-pilot-pack-experimental-segment-isolation-card-20260315.md`
- `03-execution/31-phase-n3n-tachibana-pilot-pack-migration-boundary-card-20260315.md`
- `03-execution/32-phase-n3o-tachibana-pilot-pack-campaign-closeout-card-20260315.md`
- `03-execution/records/05-phase-n1-7-fb-stability-and-purity-record-20260312.md`
- `03-execution/records/09-phase-n1-11-bof-pinbar-quality-provenance-record-20260313.md`
- `03-execution/records/10-phase-n1-12-bof-pinbar-stability-or-no-go-record-20260313.md`
- `03-execution/records/04-phase-n1-8-tachibana-contrary-alpha-record-20260312.md`
- `03-execution/records/06-phase-n1-9-fb-detector-refinement-record-20260312.md`
- `03-execution/records/07-phase-n1-9a-fb-boundary-stability-follow-up-record-20260312.md`
- `03-execution/records/08-phase-n1-10-sb-refinement-or-no-go-record-20260312.md`
- `03-execution/records/00-normandy-interim-conclusions-20260312.md`
- `03-execution/records/12-phase-n2-bof-control-baseline-exit-decomposition-record-20260313.md`
- `03-execution/records/13-phase-n2a-targeted-trailing-stop-follow-up-record-20260313.md`
- `03-execution/records/14-phase-n2a-2-profit-gated-micro-sweep-record-20260313.md`
- `03-execution/records/15-phase-n2a-3-two-stage-trailing-probe-record-20260313.md`
- `03-execution/records/16-phase-normandy-campaign-closeout-record-20260313.md`
- `03-execution/records/17-phase-n3-tachibana-tradebook-contract-record-20260315.md`
- `03-execution/records/18-phase-n3a-tachibana-january-sample-blocker-record-20260315.md`
- `03-execution/records/19-phase-n3b-tachibana-rear-pages-source-correction-record-20260315.md`
- `03-execution/records/20-phase-n3c-tachibana-semantics-and-replay-ledger-record-20260315.md`
- `03-execution/records/21-phase-n3d-emotionquant-module-reuse-triage-record-20260315.md`
- `03-execution/records/22-phase-n3e-tachibana-state-transition-candidate-table-record-20260315.md`
- `03-execution/records/23-phase-n3f-tachibana-validation-rule-candidate-matrix-record-20260315.md`
- `03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
- `03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
- `03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
- `03-execution/records/27-phase-n3j-tachibana-pilot-pack-runner-implementation-record-20260315.md`
- `03-execution/records/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-record-20260315.md`
- `03-execution/records/29-phase-n3l-tachibana-pilot-pack-unit-regime-overlay-record-20260315.md`
- `03-execution/records/30-phase-n3m-tachibana-pilot-pack-experimental-segment-isolation-record-20260315.md`

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
28. 第十一张执行卡：围绕 `Tachibana` 做 refinement / backlog retention formal gate。
29. 第十二张执行卡：围绕 `BOF_CONTROL` 打开 `N2 baseline lane`，先做 baseline exit decomposition。
30. 第十三张执行卡：围绕 `BOF_CONTROL` 当前最可疑的 `trailing-stop` 路径做 targeted follow-up，不重开 entry family。
31. `N1.8` 首轮 formal readout：固定 `TACHI_CROWD_FAILURE` 当前只是 observation-only，而不是独立 alpha 胜者。
32. `N1.9` 首轮 formal readout：固定 `FB_BOUNDARY` 是当前 retained branch，但它仍需先做 stability follow-up，不能直接打开 `N2`。
33. `N1.9A` 首轮 formal readout：固定 `FB_BOUNDARY` 当前仍不够稳，主队列优先级切到 `SB refinement or no-go`。
34. `N1.10` 首轮 formal readout：固定 `SB` 当前 full detector 路线 `no-go`，但保留 `SB_SMALL_W_MID_STRENGTH` 为窄 watch branch。
35. `N1.11` 首轮 formal readout：固定 `BOF_KEYLEVEL_PINBAR` 为 retained branch，`BOF_KEYLEVEL_STRICT` 只保留 candidate-level positive read，`BOF_PINBAR_EXPRESSION` 直接 no-go。
36. `N1.12` 首轮 formal readout：固定 retained `BOF_KEYLEVEL_PINBAR` 在长窗下仍属 `branch_no_go`，`BOF_CONTROL` 继续保持唯一 baseline，`N2` 不打开。
37. 当前阶段性结论、对象分层与延后研究清单。
38. `N2 baseline lane` 第一轮 formal readout：固定 `BOF_CONTROL` 不是买错，`execution friction` 不是主因，而当前最可疑的是 `trailing-stop` 的 mixed damage。
39. `N2A` 第一轮 formal readout：固定当前 trailing-stop 伤害更像 `small_cluster_of_outlier_truncation`，而不是普遍存在的 `repeatable trend-premature-exit`，因此不支持当前主线立刻全局取消 trailing-stop。
40. `N2A-2` profit-gated micro-sweep formal readout：固定 `PROFIT_GATED_TRAIL_25P` 是当前最平衡的 preservation 候选，但它仍然只是 `partial trade-off`，不支持默认 trailing-stop 语义改写，也不解锁 `promotion lane`。
41. `N2A-3` two-stage trailing probe formal readout：固定 `POST_15P_TRAIL_9P` 是当前更干净的局部机制候选，但整体仍然属于 `no_clean_preservation_candidate_yet`，因此只保留 `N2A` 的 targeted diagnosis，不改默认 trailing-stop 语义，也不解锁 `promotion lane`。
42. `Normandy campaign closeout` formal readout：固定当前战役所有已定义 cards 均已闭环，当前主队列清空；可迁回主线的是治理边界与负面约束，不是新的默认参数；若未来继续，必须新开 `targeted hypothesis` 或 `mainline migration package`。
43. `Tachibana quantifiable execution system` implementation spec：把立花方法从单一 contrary alpha 假说重新整理为可量化的执行 doctrine。
44. `N3` formal record：固定交易谱第一轮正确入口是 `ledger scaffold`，而不是直接声称“原始交易账已经可机读”。
45. `N3a` formal blocker：写死 `1975-01` 当前只能作为 manual backfill sample，不能冒充事实真值页。
46. `N3b` formal source correction：写死后页月表才是真实事实源，并正式承认 `long / short` 双侧未平仓语义。
47. `N3c` formal record：固定执行语义证据表与 replay ledger，确认立花方法已可被回放为 state-transition-aware ledger。
48. `N3d` formal triage：把 `EmotionQuant-gamma` 内对立花验证的直接复用、改造复用、退出主线资产正式分流。
49. `N3e` formal record：把立花方法冻结为 `9` 个状态迁移候选簇，并明确哪些可迁回主线、哪些只能保留为结构类对象。
50. `N3f` formal record：把候选簇进一步压成 `R1-R10` 规则候选矩阵，并写死当前可诚实开跑的 pilot subset。
51. `N3g` opening note：把 `R4 + R5 + R6 + R7 + R10` pilot-pack 的正式边界、control baseline、第三战场复用链与禁止偷带项写死，并把下一步收敛到 `reduce-to-core + cooldown` executable pilot。
52. `N3h` executable matrix：把 pilot-pack 正式拆成 `E1/E2/E3/E4` 四个执行包，并写死哪些现在可跑、哪些只差轻量扩展。
53. `N3i` implementation scaffold：把 `E1` 固定成 Normandy thin runner、把 `E2` 固定成 engine `signal_filter hook`、把 `E3` 固定成 payload-level tag glue。
54. `N3j` runner implementation：把 pilot-pack matrix/digest runner、same-code cooldown hook 与最小 smoke evidence 正式落库，并把默认运行路径对齐到 `docs/reference/operations` 的三目录纪律。
55. `N3k` formal cooldown matrix：把 `CD0 / CD2 / CD5 / CD10` 在正式窗口下跑成 cooldown scorecard，写死 `CD2 = no-op`、`CD5 = first effective cooldown`、`CD10 = provisional cooldown leader`。
56. `N3l` unit-regime overlay：把正式窗口下的 `fixed_notional` operating pair 与 `single_lot` floor pair 并排写定，正式收窄为 `FIXED_NOTIONAL_CONTROL` 仍是唯一 operating regime、`SINGLE_LOT_CONTROL` 只保留为 floor sanity、`TRAIL_SCALE_OUT_25_75` 在 floor 下退化、`reduced_unit_scale` 仍只是 payload tag。
57. `N3m` experimental-segment isolation：把 `experimental_segment_policy = isolate_from_canonical_aggregate` 落成 digest 级 aggregate 隔离规则，正式写死 canonical aggregate 只保留 canonical control/proxy pair，而 cooldown、floor 与 noncanonical side references 全部只配做 experimental sidecar。

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

`保持 blueprint 主线结论不变，以 legacy_bof_baseline 为当前默认运行口径，在继承同一套三目录 / 执行库 / 旧库 / TuShare 双通道纪律的前提下，先独立证明 PAS raw alpha，再在同一套 Broker 下把 BOF family quality 和 exit damage 读干净，同时把 Tachibana doctrine 收成可回放、可迁移的 execution subset。`

再压缩一句：

`Normandy 是研究线，不是版本线；它负责找答案，不负责直接改写主线。`
