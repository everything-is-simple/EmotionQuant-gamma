# FB Second-Layer Provenance Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `Normandy / N1.6 FB 第二层 provenance`

---

## 1. 定位

本文不是重新打开 `RB_FAKE / SB / FB` 的第一轮比较。

`N1.5` 已经回答了第一层问题：

`谁最像第二个自带 alpha 的人。`

当前答案已经固定为：

`FB`

因此 `N1.6` 不再回答“谁赢”，而是专门回答：

`FB 当前这条正向 edge，到底是独立补充型 alpha，还是小样本 / 单一环境 / 特定 timing 偶然产物。`

---

## 2. 当前已知前提

截至 `2026-03-12`，下面这些结论已经固定：

1. `BOF` 继续是当前 baseline
2. `FB` 是首轮唯一通过 `second alpha candidate` 门槛的非 `BOF` 候选
3. `RB_FAKE` 当前更像 `BOF` 的 Volman 化子集
4. `SB` 独立性强，但当前 detector 还没有收缩出正向 edge

因此 `N1.6` 的唯一对象固定为：

1. `BOF_CONTROL`
2. `FB`

---

## 3. 当前要回答的四个问题

`N1.6` 固定只回答四个问题：

1. `FB` 的正向 edge 是否显著依赖单一环境桶
2. `FB` 是不是只是 `BOF` 没碰到的稀疏 timing 子集
3. `FB` 当前样本密度是否只够“候选成立”，还不够“稳定成立”
4. `FB` 下一步应该进入：
   - 更深一层 provenance
   - 受控 exit decomposition
   - 还是先做 detector refinement

---

## 4. 当前实验允许做什么

当前实验固定允许：

1. 读取 `N1.5` 已完成的 matrix / digest
2. 对 `FB` 与 `BOF_CONTROL` 输出 focused dossier
3. 摘出 `FB` 的环境桶依赖、增量 trade、overlap 和样本风险
4. 输出下一步研究建议

当前实验固定不允许：

1. 重新改写 `BOF` baseline
2. 跳过 `FB` 第二层 provenance 直接把它升成主线
3. 顺手把 `SB / RB_FAKE` 又拉回同一轮竞争
4. 在这一层重新打开 `MSS / Broker` 微调

---

## 5. 当前证据对象

`N1.6` 当前默认只消费下面两份产物：

1. `normandy_volman_alpha_matrix_*__volman_alpha_matrix.json`
2. `normandy_volman_alpha_digest_*__volman_alpha_digest.json`

在这两份产物之上，`N1.6` 需要再生成一份 focused evidence：

3. `fb_candidate_report`

---

## 6. 当前证据要求

`FB dossier` 至少要覆盖：

1. `FB` vs `BOF_CONTROL` 的核心指标对照
2. `FB` 的环境桶拆解
3. `FB` 的 overlap / incremental trade 结论
4. `FB` 的风险标记
5. `FB` 的下一步研究建议

这里的风险标记当前至少要允许包括：

1. `low_sample_count`
2. `dominant_bucket_dependency`
3. `bullish_failure_observed`
4. `edge_below_bof_control`

---

## 7. 出场条件

`N1.6` 只有在以下条件之一满足时才允许出场：

1. 已明确 `FB` 是值得进入更深 provenance 的补充型 alpha
2. 已明确 `FB` 当前只是脆弱候选，需要先做 detector refinement

无论哪种结果，都必须留下正式 record。

---

## 8. 当前一句话方案

`以 BOF_CONTROL 为固定 baseline，不再重跑第一轮竞争，而是围绕 FB 输出 focused dossier，专门回答它到底是稳定补充型 alpha，还是暂时成立的小样本候选。`
