# Normandy Interim Conclusions

**状态**: `Active`  
**日期**: `2026-03-13`  
**对象**: `第二战场当前阶段性研究结论与后续研究清单`

---

## 1. 当前已经可以写死的结论

截至 `2026-03-13`，`Normandy` 当前已经可以固定下面这些结论：

1. `BOF` 是当前 `PAS raw alpha baseline`
2. `BOF` 接下来不再作为“待证对象”，而是作为所有候选的固定对照与尺子
3. `BPB` 当前 standalone detector 路线视为 `no-go`
4. `FB family` 已完成 refinement 与 focused stability follow-up：当前 retained branch 固定为 `FB_BOUNDARY`，但它已被正式降级为 `watch candidate / not-n2-ready`
5. `RB_FAKE` 当前更像 `BOF` 的 Volman 化窄子集，不像第二条独立 alpha 链
6. `SB` 已完成 `N1.10` formal readout：当前 full detector 路线 `no-go`，但保留 `SB_SMALL_W_MID_STRENGTH` 为窄 watch branch
7. `PB / TST / CPB` 暂不再以“谁接班 BOF”的方式继续平行竞争
8. `TACHI_CROWD_FAILURE` 当前 minimal contract 已形成可审判样本，但首轮长窗裁决仍是 `observation-only`
9. `BOF family` 已完成 `N1.11 / N1.12` formal readout：`BOF_KEYLEVEL_PINBAR` 虽在 `N1.11` 中成为 retained branch，但 `N1.12` 已正式裁定其 `branch_no_go`
10. `BOF_CONTROL` 当前继续保持 `Normandy` 唯一 baseline；`N2 baseline lane` 第一轮长窗 formal readout 已完成，当前正式答案是：`不是买错`、`execution friction` 不是主因、当前最可疑的是 `trailing-stop` 的 `mixed / concentrated damage`
11. `N2A targeted trailing-stop follow-up` 第一轮 formal readout 已完成，当前正式裁决是：`small_cluster_of_outlier_truncation`，而不是 `repeatable trend-premature-exit pattern`
12. `N2` 的 `promotion lane` 当前仍没有可放行对象，继续锁住；当前不把 baseline diagnosis 或 `N2A` follow-up 误读成 branch promotion

---

## 2. 当前对象分层

| 对象 | 当前定位 | 当前处理 |
|---|---|---|
| `BOF` | 固定 baseline / control | 所有新候选的统一对照尺；并作为 `N2 baseline lane` 的固定 entry set；第一轮 formal readout 已完成，当前结论是 `not buy wrong / trailing-stop mixed damage / friction not material`；`N2A` 已进一步把它细化为 `small_cluster_of_outlier_truncation` |
| `BOF_KEYLEVEL_PINBAR` | `n1_11_retained_but_n1_12_branch_no_go` | 结束当前升格，回到 `BOF_CONTROL` |
| `BOF_KEYLEVEL_STRICT` | 正向读数存在，但未成为 retained 主位 | 保留为观察分支，不进入主队列 |
| `BOF_PINBAR_EXPRESSION` | 长窗正式 `no-go` | 退出 `BOF` quality 主队列 |
| `FB_BOUNDARY` | `retained_watch_candidate_not_n2_ready` | 保留 retained branch 身份，但主队列不继续优先深挖，`N2` 暂不打开 |
| `FB_CLEANER` | cleaner textbook branch but not carrying current edge | 退出 `FB` 主队列，保留为观测分支 |
| `SB` | `full_detector_no_go_watch_branch_only` | 冻结 full detector 路线；仅保留 `SB_SMALL_W_MID_STRENGTH` 为 watch / backlog 分支 |
| `RB_FAKE` | `BOF` 的 Volman 化窄子集 | 进入观察池，不抢第二 alpha 主位 |
| `PB / TST / CPB` | 未通过 standalone provenance | 进入观察池，延后处理 |
| `BPB` | 当前 standalone `no-go` | 冻结当前 detector 路线 |
| `TACHI_CROWD_FAILURE` | 已形成首轮可审判样本，但未形成独立 contrary alpha | 保留为 Tachibana refinement / backlog 对象 |

这里的 `BPB no-go` 只针对：

`当前 detector / 当前 standalone route`

它不等于：

`从 PAS taxonomy 中永久删除 BPB`

---

## 3. BOF 接下来该扮演什么角色

`BOF` 当前已经从“候选”变成“尺子”。

它接下来的职责固定为：

1. 所有新候选的固定 baseline
2. overlap / incremental / exit 对照基准
3. 执行语义变化时的健康检查对象

也就是说：

`BOF 接下来不再反复被拖回候选池，而是负责给所有新候选提供比较基准。`

---

## 4. 当前研究优先级

### 4.1 第一优先级：`N2 baseline lane / targeted trailing-stop follow-up`

当前状态：

`第一轮长窗 formal readout 已完成；N2A targeted follow-up 也已完成第一轮 formal readout。`

当前已经可以写死：

1. `BOF_CONTROL` 不是 `买错`
2. `execution friction` 当前不是主因
3. `exit damage` 当前确实存在，但 baseline lane 读成 `mixed / concentrated damage`
4. `N2A` 已进一步把当前最可疑路径固定为：`small_cluster_of_outlier_truncation`
5. 当前没有证据支持 `repeatable trend-premature-exit pattern`
6. `N2 promotion lane` 继续锁住

当前对应执行卡与 record：

1. `normandy/03-execution/13-phase-n2a-targeted-trailing-stop-follow-up-card-20260313.md`
2. `normandy/03-execution/records/13-phase-n2a-targeted-trailing-stop-follow-up-record-20260313.md`

若继续沿本 lane 前推，研究内容只允许是：

1. 针对 `fat-tail preservation` 做更细的 targeted decomposition
2. 区分 `保护回撤` 与 `错杀 fat-tail winners` 的真实边界
3. 不把 `STOP_ONLY` 的 uplift 粗暴翻译成“主线现在就该取消 `trailing-stop`”

预计时间：

`第一轮 formal readout 已完成；是否继续精化，取决于主队列治理裁决`

要求深度：

`若继续，必须把 current trailing-stop damage 继续读成比 outlier truncation 更细的正式证据，而不是直接全局改写语义。`

### 4.2 第二优先级：`Tachibana detector refinement or backlog retention`

研究内容：

1. 承认 `TACHI_CROWD_FAILURE` 当前只保留为 observation / backlog
2. 不把当前 minimal contract 的失败误写成“立花理论整体失败”
3. 把这条线从“口头保留”推进到正式 `refinement` 或正式 `backlog retention`

预计时间：

`延后排队，但应完成治理收口`

要求深度：

`足以决定 Tachibana 这条线是继续 formalize，还是明确留在 backlog。`

### 4.3 第三优先级：`观察池 / watch branches 治理收口`

研究内容：

1. 承认 `FB_BOUNDARY / SB_SMALL_W_MID_STRENGTH / BOF_KEYLEVEL_STRICT` 当前都不属于主队列可直推对象
2. 区分：
   - `watch candidate`
   - `watch backlog branch`
   - `not retained but worth留档`
3. 避免把观察池对象重新误拉回大混战

预计时间：

`1 ~ 2` 天

要求深度：

`足以让当前对象分层在文档和主队列口径上彻底一致。`

### 4.4 第四优先级：`N2 promotion lane`

前提：

只有当未来重新出现 `eligible_for_n2` 的稳定 retained object 时才允许打开。

研究内容：

1. 当前继续保持锁定状态，不进入执行
2. 不把 `BOF quality branch` 的局部亮点误读成 `N2 ready`
3. 保持 `baseline diagnosis lane` 与 `promotion lane` 明确分离

预计时间：

`未解锁，不排期`

要求深度：

`只有在出现新的稳定 retained object 时才要求达到这个深度。`

### 4.5 第五优先级：`Volman deferred queue`

研究内容：

1. `RB_TRUE / IRB / DD / BB / ARB` 当前继续只保留在后备研究队列
2. 不把 sidecar / enhancer 类对象误写成新一轮正式 detector 主队列
3. 等主队列和 backlog 口径彻底收口后再讨论是否重开

预计时间：

`延后排队，不占主队列`

要求深度：

`只保留研究清单价值，不先占用执行资源。`

---

## 5. Volman 延后研究清单

以下对象当前不跑正式长窗，但已经正式进入研究清单，后续不得遗忘：

1. `RB_TRUE`
   - 角色：真突破 continuation
   - 当前定位：晚于 `RB_FAKE / FB / SB` 的第二层候选
2. `IRB`
   - 角色：handle / boundary breakout timing refinement
   - 当前定位：更像 sidecar，不先独立 detector 化
3. `DD`
   - 角色：hold / test 的 micro trigger
   - 当前定位：更像 sidecar，不先独立 detector 化
4. `BB`
   - 角色：pressure / compression enhancer
   - 当前定位：质量层，不先独立 detector 化
5. `ARB`
   - 角色：复合型结构 bias
   - 当前定位：后期 composite research object

这一组对象当前统一归类为：

`Volman deferred queue`

---

## 6. Tachibana 研究清单

`立花义正` 当前也已经正式纳入后续研究清单。

但它的定位必须写死：

1. 它不是当前 `PAS` taxonomy 的新形态来源
2. 它不是当前 `MSS` 的直接替代方案
3. 它更像一套：
   - contrary doctrine
   - crowd-extreme observation framework
   - execution / risk rhythm discipline

当前更合理的后续研究入口是：

1. `TACHI_CROWD_FAILURE`
   - 当前定位：第一条最小可执行 entry 假设
2. `Tachibana contrary theory dossier`
   - 当前定位：理论骨架留档
3. `extreme sentiment sample study`
   - 当前定位：若第一轮 entry 成立，再深挖样本族
4. `休息 / 撤退 / 试探仓位` 的执行纪律研究
   - 当前定位：第二层，不进入首轮 entry detector

这条线当前统一归类为：

`Outside-PAS but Normandy-relevant research queue`

---

## 7. 当前不该做的事

当前阶段明确不建议：

1. 再把 `PB / TST / CPB / SB / FB` 一起拖进新一轮大混战
2. 继续围绕 `BPB` 烧时间
3. 把 `BOF quality split` 的局部亮点误读成“已经可以开 N2 promotion lane”
4. 把 `STOP_ONLY` 的巨大 uplift 粗暴翻译成“主线现在就该取消 trailing-stop”
5. 把 `Tachibana` 粗暴翻译成“把 PAS 反着做”

---

## 8. 当前一句话路线图

BOF 作为尺子固定，BOF family quality gate 已经读完且当前结论是 baseline-only；`N2 baseline lane` 的第一轮长窗 formal readout 已回答“不是买错，主要可疑点在 trailing-stop 的 mixed damage”，`N2A` 又把它进一步读成“少数 fat-tail winners 被提前砍掉”，当前主队列若继续前推，只能沿 `fat-tail preservation` 深挖，而 `N2 promotion lane` 继续锁住。
