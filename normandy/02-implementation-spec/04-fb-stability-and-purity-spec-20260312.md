# FB Stability And Purity Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `Normandy / N1.7 FB 稳定性与 purity 审核`

---

## 1. 定位

`N1.7` 不是重新打开 `BOF / FB / SB` 的第一轮竞争，也不是直接进入全量 `exit decomposition`。

它只回答一件事：

`FB 这条当前成立的第二 alpha 候选，是否已经稳定到值得继续深挖，还是仍然停留在脆弱候选。`

---

## 2. 当前已知前提

截至 `2026-03-12`，下面这些结论已经固定：

1. `BOF` 继续是当前 `PAS raw alpha baseline`
2. `BPB` 当前 standalone detector 路线视为 `no-go`
3. `FB` 是首轮唯一通过 `second alpha candidate` 门槛的非 `BOF` 候选
4. `FB dossier` 已给出四个风险标记：
   - `low_sample_count`
   - `dominant_bucket_dependency`
   - `bullish_failure_observed`
   - `edge_below_bof_control`
5. `SB` 当前不退场，但先进入延后 refinement 队列

因此 `N1.7` 当前固定只围绕：

1. `BOF_CONTROL`
2. `FB`

---

## 3. 当前要回答的四个问题

`N1.7` 固定只回答四个问题：

1. `FB` 的正向 edge 是否在多个环境桶中都可复现
2. `FB` 的“首次回撤”语义是否足够纯，还是被宽 detector 混入了太多杂质
3. `FB` 对 `BOF` 是真正的补充型 alpha，还是只是低频偶然样本
4. `FB` 下一步应进入：
   - `N2 exit decomposition`
   - `detector refinement`
   - 还是先停留在候选层

---

## 4. 当前实验允许做什么

当前实验固定允许：

1. 读取 `N1.5` / `N1.6` 已完成的 matrix / digest / dossier
2. 对 `FB` 做环境桶切片、样本分层和 purity audit
3. 对 `FB` 与 `BOF_CONTROL` 做 overlap / incremental / exit-ready 对照
4. 输出稳定性结论与下一步建议

当前实验固定不允许：

1. 重新改写 `BOF` baseline
2. 顺手把 `SB / RB_FAKE / PB / TST / CPB` 拉回本轮主比较集
3. 因 `FB` 当前成立就直接升格主线
4. 在本轮重新打开 `MSS / Broker` 大范围微调

---

## 5. 当前证据对象

`N1.7` 当前默认消费下面三类上游产物：

1. `normandy_volman_alpha_matrix_*__volman_alpha_matrix.json`
2. `normandy_volman_alpha_digest_*__volman_alpha_digest.json`
3. `*__fb_candidate_report.json`

在此基础上，本轮建议新增两类 focused evidence：

4. `fb_stability_report`
5. `fb_purity_audit`

---

## 6. 当前证据要求

`FB stability / purity` 至少要覆盖：

1. `FB` vs `BOF_CONTROL` 的核心指标与样本密度对照
2. `FB` 的环境桶切片
3. `FB` 的 overlap / incremental trade 结论
4. `FB` 的 first-pullback purity 读数
5. `FB` 的下一步去向裁决

这里的 purity 审核当前至少要允许回答：

1. `FB` 是否过度依赖单一“突然爆发 + 浅回撤”样本
2. `FB` 是否把过多普通 `PB / continuation` 杂样混入 detector
3. `FB` 的失败样本是否主要集中在同一类 market state

---

## 7. 出场条件

`N1.7` 只有在以下条件之一满足时才允许出场：

1. 已明确 `FB` 值得进入 `N2 exit decomposition`
2. 已明确 `FB` 仍是脆弱候选，需要先做 detector refinement

无论哪种结果，都必须留下正式 record。

---

## 8. 当前一句话方案

`以 BOF_CONTROL 为固定尺子，不再重开第一轮竞争，而是把 FB 从“合格候选”继续推进到“稳定候选”或“需收缩 detector 的脆弱候选”。`
