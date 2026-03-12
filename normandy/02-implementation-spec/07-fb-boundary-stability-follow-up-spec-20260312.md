# FB Boundary Stability Follow-up Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `Normandy / N1.9A FB_BOUNDARY focused stability follow-up`

---

## 1. 定位

`N1.9A` 是 `N1.9` 的直接 follow-up。

它不再回答：

`FB cleaner 还是 boundary 在 carrying edge。`

这个问题已经由 `N1.9` 回答完毕。

`N1.9A` 只回答：

`既然 retained branch 已经固定为 FB_BOUNDARY，它当前是否真的稳到可以打开 N2。`

---

## 2. 当前已知前提

截至 `2026-03-12`，下面这些结论已经固定：

1. `BOF` 继续是 `PAS raw alpha baseline`
2. `N1.9` 已把 `FB` family 的 retained branch 固定为 `FB_BOUNDARY`
3. `FB_CLEANER` 已退出 `FB` 主队列
4. `N1.9` 仍把 `FB_BOUNDARY` 标为：
   - `still_fragile_after_refinement`
   - `boundary_stability_follow_up_before_n2`

因此 `N1.9A` 当前的职责不是继续 split detector，而是把 retained branch 的稳定性问题正式读完。

---

## 3. 当前要回答的问题

`N1.9A` 固定只回答三个问题：

1. `FB_BOUNDARY` 的负切片是否只是局部噪声，还是跨年仍在重复
2. `FB_BOUNDARY` 的负 trade 是否集中在少数 isolated accident，还是已经跨多个年份出现
3. 在以上问题回答后，`N2` 是否继续锁住

---

## 4. 当前实验允许做什么

当前实验固定允许：

1. 继承 `fb_refinement_matrix` 与 `fb_refinement_digest`
2. 读取同一 working DB 的 lifecycle pairing
3. 输出 focused `fb_boundary_stability_report`
4. 固定 retained branch 的下一步去向

当前实验固定不允许：

1. 重新打开 `FB_CLEANER`
2. 再次重跑 `FB detector refinement matrix`
3. 把 `SB / RB_FAKE / PB / TST / CPB` 拉回本卡
4. 在本卡顺手开始 `N2`

---

## 5. 当前证据对象

`N1.9A` 当前默认消费：

1. `fb_refinement_matrix`
2. `fb_refinement_digest`

本卡新增正式 evidence：

3. `fb_boundary_stability_report`

---

## 6. 出场条件

`N1.9A` 只有在以下条件之一满足时才允许出场：

1. 已明确 `FB_BOUNDARY` 可以打开 `N2`
2. 已明确 `FB_BOUNDARY` 仍不应打开 `N2`，并给出主队列后续优先级调整

---

## 7. 当前一句话方案

`围绕 retained branch FB_BOUNDARY 再做一轮 focused stability slice，把“是否能开 N2”这个问题正式回答完。`
