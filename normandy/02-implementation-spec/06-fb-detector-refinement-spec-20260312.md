# FB Detector Refinement Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `Normandy / N1.9 FB detector refinement`

---

## 1. 定位

`N1.9` 是 `N1.7` 的直接后续卡。

它不再回答：

`FB 有没有 alpha。`

它只回答：

`当前 FB 的 alpha，到底是 cleaner(0/1 touch) first-pullback 在撑，还是 boundary(2 touch) 分支在撑。`

---

## 2. 当前已知前提

截至 `2026-03-12`，下面这些结论已经固定：

1. `BOF` 继续是 `PAS raw alpha baseline`
2. `FB` 继续保留为第二个 alpha 候选
3. `N1.7` 已固定：
   - `stability_status = fragile_candidate_not_exit_ready`
   - `purity_verdict = boundary_loaded_detector_refinement_required`
4. `FB` 当前不能直接进入 `N2`
5. `N1.7` 已把下一步固定为：
   - `FB cleaner(0/1 touch)`
   - `FB boundary(2 touch)`
   的正式拆分 replay

---

## 3. 当前要回答的问题

`N1.9` 固定只回答三个问题：

1. `FB cleaner(0/1 touch)` 是否保得住总 EV
2. `FB boundary(2 touch)` 是否才是当前真正 carrying edge 的分支
3. 若胜出分支成立，它是否已经足够稳到可以直接打开 `N2`

---

## 4. 当前实验允许做什么

当前实验固定允许：

1. 继承 `N1.5` 长窗 window 与 `N1.7` 的 purity 结论
2. 把 `FB detector` 参数化为：
   - `FB_CLEANER`
   - `FB_BOUNDARY`
3. 用同一条 `Normandy Volman` 回测链路分别 replay
4. 输出 `fb_refinement_matrix`
5. 输出 `fb_refinement_digest`
6. 固定 retained branch 与下一步裁决

当前实验固定不允许：

1. 重新打开 `RB_FAKE / SB / PB / TST / CPB` 的平行竞争
2. 把 `FB` 当前 family-level alpha 直接翻译成 `N2 ready`
3. 顺手重写 `BOF` baseline
4. 把 `MSS / Broker` 调参拉回本卡

---

## 5. 当前证据对象

`N1.9` 当前默认消费：

1. `N1.7` record
2. `fb_stability_report`
3. `fb_purity_audit`
4. `normandy_volman_alpha_matrix_*__volman_alpha_matrix.json`

本卡新增正式 evidence：

5. `fb_refinement_matrix`
6. `fb_refinement_digest`

---

## 6. 出场条件

`N1.9` 只有在以下条件之一满足时才允许出场：

1. 已固定 `FB_BOUNDARY` 或 `FB_CLEANER` 为 retained branch
2. 已固定 `FB family` 在 refinement 后不再保留主队列位置

无论哪种结果，都必须留下正式 record。

---

## 7. 当前一句话方案

`把 family-level FB 拆成 cleaner 与 boundary 两支，先查清哪一支真正在 carrying edge，再决定 Normandy 是否继续围绕该 retained branch 往下走。`
