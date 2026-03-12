# Normandy N1.5 第二个 Alpha 结论记录

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1.5`  
**对象**：`Volman 第二个自带 alpha 候选结论固定`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.5` 的首轮 `Volman second alpha search` 结论固定下来。

本记录只回答当前系统里的一个问题：

`在 BOF 已经重新钉实为当前 baseline 之后，RB_FAKE / SB / FB 里，谁最像第二个能自己扛 raw alpha 的 entry object。`

本文不改写：

1. `blueprint/` 主线 SoT
2. `BOF` 作为当前 baseline 的地位
3. `Normandy` 后续对 `exit damage decomposition` 的问题边界

---

## 2. 参考依据

### 2.1 来源语义参考

1. `docs/Strategy/PAS/volman-pas-alpha-screening.md`
2. `docs/Strategy/PAS/volman-pas-v0-research-card-20260312.md`
3. `docs/Strategy/PAS/volman-rb-sb-fb-minimal-contract-note-20260312.md`
4. `docs/Strategy/PAS/bof-firstborn-record-20260312.md`

这些参考对当前问题给出的固定边界是：

1. `RB_FAKE` 属于 `failure / reversal family`
2. `FB` 属于 `first pullback continuation family`
3. `SB` 属于 `second break / second failure liquidation family`
4. `SB` 必须进入第一批候选，但不能因为主观偏爱就提前宣布胜出
5. 第二个 alpha 的判断标准，不是“谁看起来更像 BOF”，而是“谁能独立交出正向 raw alpha 证据”

### 2.2 实证证据参考

1. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__volman_alpha_matrix.json`
2. `normandy/03-execution/evidence/normandy_volman_alpha_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t015510__volman_alpha_digest.json`
3. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`

首轮矩阵固定比较：

1. `BOF_CONTROL`
2. `RB_FAKE`
3. `SB`
4. `FB`

---

## 3. N1.5 长窗结果

在 `2023-01-03` 到 `2026-02-24` 的统一长窗口上，首轮结果如下：

| Label | Trade Count | EV | PF | MDD | Participation | Overlap vs BOF | Incremental Trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BOF_CONTROL` | 277 | 0.01609 | 2.6121 | 0.13267 | 0.80523 | 1.00000 | 0 |
| `RB_FAKE` | 144 | -0.00978 | 1.7265 | 0.15913 | 0.97297 | 0.80556 | 28 |
| `SB` | 648 | -0.01455 | 2.0909 | 0.64103 | 0.15588 | 0.00000 | 648 |
| `FB` | 33 | 0.01450 | 3.4433 | 0.05908 | 1.00000 | 0.00000 | 33 |

当前 digest 的正式判断为：

1. `provenance_leader = FB`
2. `second_alpha_candidates = [FB]`
3. `FB` 当前满足：
   - 正 `EV`
   - 样本密度门槛
   - 增量 trade 门槛
   - 独立于 `BOF_CONTROL` 的低 overlap 条件

---

## 4. 三个候选的定性结论

### 4.1 `FB`

`FB` 当前是首轮唯一通过门槛的非 `BOF` 候选。

它的意义不是“比 `BOF` 更强”，而是：

1. 它属于不同于 `BOF` 的 `continuation family`
2. 它在当前长窗里保持正 `EV`
3. 它与 `BOF_CONTROL` 没有重叠交易，说明它不是 `BOF` 的简单重复记分
4. 它虽然样本量不大，但已经跨过 `min_trade_count=20` 的当前实验门槛

因此，`FB` 当前最像：

`第二个具备独立 raw alpha 资格的 entry object。`

### 4.2 `RB_FAKE`

`RB_FAKE` 这轮没有通过第二个 alpha 门槛。

原因很直接：

1. `EV` 为负
2. 与 `BOF_CONTROL` 的 overlap 达到 `0.80556`
3. 增量 trade 虽然大于 20，但不足以抵消其负向 edge

这说明当前版本的 `RB_FAKE` 更像：

1. `BOF` 的 Volman 收窄子集
2. 或 `BOF` 的结构细化候选

而不是当前已经独立站住的第二条 alpha 链。

### 4.3 `SB`

`SB` 这轮也没有通过门槛，而且失败得比 `RB_FAKE` 更明确。

原因是：

1. 它虽然有大量增量 trade
2. 与 `BOF_CONTROL` 完全不重叠
3. 但 `EV` 为负，且 `MDD` 明显过大

这意味着当前版本的 `SB` 问题不在“没有独立性”，而在：

`独立性很强，但 entry edge 还没有被当前 detector 定义成正向 alpha。`

所以本轮对 `SB` 的正式态度应固定为：

1. 不能升格为第二个 alpha
2. 也不能因为失败就从 `Volman` 候选家族里抹掉
3. 它仍值得后续做 detector 收缩、结构清洗或 regime 分桶复核

---

## 5. 正式结论

结合 `Volman PAS v0` 的对象边界与 `N1.5` 三年长窗证据，当前系统结论固定为：

1. `BOF` 继续作为当前系统的 baseline，不退位
2. `FB` 是当前第一位通过证据门槛的非 `BOF` 候选，可被正式记为：
   - `第二个自带 alpha 候选`
   - `Volman continuation family` 的首个通过者
3. `RB_FAKE` 当前不构成第二个 alpha，更像 `BOF` 的 Volman 化子集
4. `SB` 当前不构成第二个 alpha，但它失败的原因不是缺独立性，而是当前 detector 还没把它收缩成正向 edge

换句话说：

`N1.5` 的首轮答案不是 SB，也不是 RB_FAKE；当前真正站出来的人是 FB。`

---

## 6. 后续动作边界

本记录同时固定后续动作边界：

1. 下一步优先围绕 `FB` 做第二层 provenance，而不是立刻宣布切换主线
2. `FB` 后续要回答的是：
   - 它是独立补充型 alpha，还是只在某些 regime 下成立
   - 它的 edge 主要来自 first pullback 语义，还是来自更稀疏的 timing 选择
3. `SB` 可以保留为后续 detector refinement 候选，但不得在本轮证据下直接升格
4. `RB_FAKE` 后续更适合沿：
   - `BOF` 子集分层
   - `failure family` 边界细化
   继续研究，而不是继续拿它冲“第二个 alpha”名额

---

## 7. 一句话结论

在 `BOF_CONTROL / RB_FAKE / SB / FB` 的首轮 `Volman` 长窗 provenance 搜索中，`FB` 是当前唯一通过正向 edge、样本密度与增量 trade 门槛的非 `BOF` 候选，因此它被固定为当前系统里“第二个自带 alpha 候选”；`SB` 与 `RB_FAKE` 本轮均不升格。
