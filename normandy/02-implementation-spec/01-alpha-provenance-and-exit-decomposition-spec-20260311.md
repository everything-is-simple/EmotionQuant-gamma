# Alpha Provenance And Exit Decomposition Implementation Spec

**状态**: `Active`  
**日期**: `2026-03-11`  
**对象**: `第二战场当前唯一实现方案`

---

## 1. 定位

本文不是 `blueprint/` 的替代实现方案。

本文只定义第二战场当前唯一实验方案：

1. 先证明 `PAS raw alpha`。
2. 再拆 `exit damage`。
3. 暂停 `MSS` 微调。

---

## 2. 问题定义

截至 `2026-03-11`，当前仓库已经有三个确定结论：

1. `v0.01-plus` 的正式默认路径未通过 `Phase 4 Gate`。
2. `Phase 4.1` 已证明 `max_positions shrink` 是重要伤害源，但就算去掉 slot shrink，`size_only_overlay` 仍未推翻 `legacy_bof_baseline`。
3. 当前无法再靠继续调 `MSS / Broker` 小语义来回答“真实 alpha 来自哪里”。

因此当前问题重写为：

1. `PAS` 哪些 entry shape 真的有 raw alpha。
2. 当前收益到底是被 `exit` 打坏，还是被 `execution` 打坏。
3. `IRS` 是否只在高信号密度 shape 上才有价值。

---

## 3. 当前唯一方案

第二战场当前唯一方案固定为两段：

1. `N1 / PAS raw alpha provenance`
2. `N2 / Exit decomposition`

执行顺序固定为：

1. 先用最简 Broker 跑长窗口 `PAS` 矩阵。
2. 在不引入 `MSS` 的前提下确定 raw entry edge。
3. 再对同一批 entry 拆 exit 语义。
4. `IRS` 只允许作为后续对照层进入，不允许先做硬过滤。

---

## 4. 实现边界

当前实验固定允许：

1. 首轮只比较 `BOF / BPB / PB / TST / CPB / YTC5_ANY`。
2. 复用当前统一 `Broker` 内核与既有 `stop_loss + trailing_stop + T+1 Open` 出场语义，但关闭 `MSS / IRS` 的前置干预。
3. 在同一窗口中比较 entry edge、trade count、EV、PF、MDD、participation。

这里的：

1. `BOF / BPB / PB / TST / CPB` 属于 `PAS pattern type`。
2. `YTC5_ANY` 属于 `pattern_set(all five) + PAS_COMBINATION=ANY` 的实验场景。
3. 本轮不把 `BOF+PB / PB+CPB` 这类组合场景混入首轮 taxonomy 证明。

当前实验固定不允许：

1. 继续冻结新的 `MSS / Broker` 候选。
2. 把 `IRS` 拉回前置硬过滤。
3. 在第二战场里直接切换当前默认运行口径。
4. 跳过 provenance，直接宣布 `PB / CPB / YTC5_ANY` 升格为默认主线。

---

## 5. 证据要求

第二战场当前固定产出三类证据：

1. `matrix summary`
2. `entry participation / rank decomposition digest`
3. `record / gate-style narrative`

若进入 `N2 / Exit decomposition`，再增加：

1. `exit attribution`
2. `path digest`

---

## 6. 继承约束

第二战场默认继承，不再重复发明：

1. 三目录纪律。
2. 当前执行库与旧库候选区分。
3. `RAW_DB_PATH / 本地旧库优先` 口径。
4. 双 TuShare key 角色分工。
5. `T+1 Open` 执行语义。

具体继承入口固定为：

`normandy/03-execution/00-dev-data-baseline-inheritance-20260311.md`

---

## 7. 当前一句话方案

当前第二战场的一句话方案可以压缩为：

`先在无 MSS / 无 IRS、但同一套 Broker 出场语义下证明 PAS raw alpha 来自哪里，再对同一批 entry 拆 exit damage。`
