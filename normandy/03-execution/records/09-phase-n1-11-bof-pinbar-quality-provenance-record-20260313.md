# Normandy N1.11 BOF Pinbar Quality Provenance Record

**日期**：`2026-03-13`  
**阶段**：`Normandy / N1.11`  
**对象**：`BOF family broker-frozen quality provenance formal readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.11` 的 `BOF pinbar quality provenance` 结论固定下来。

本记录只回答两个问题：

1. 在同一套 `Broker` 出场语义下，`BOF` family 内部是否存在一个比 `BOF_CONTROL` 更值得保留的 quality branch
2. 若存在 retained branch，哪一支应进入 `N1.12 / stability or no-go`

---

## 2. 参考依据

### 2.1 上游边界

1. `normandy/02-implementation-spec/09-bof-pinbar-broker-frozen-go-spec-20260312.md`
2. `normandy/03-execution/09-phase-n1-11-bof-pinbar-quality-provenance-card-20260312.md`
3. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_bof_quality_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t132536__bof_quality_matrix.json`
2. `normandy/03-execution/evidence/normandy_bof_quality_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t143141__bof_quality_digest.json`

---

## 3. N1.11 核心结果

`bof_quality_digest` 当前已经把本轮结论固定为：

1. `family_verdict = retained_branch_selected`
2. `decision = advance_retained_branch_to_n1_12`
3. `retained_branch = BOF_KEYLEVEL_PINBAR`
4. `retained_branches = [BOF_KEYLEVEL_PINBAR, BOF_KEYLEVEL_STRICT]`

这意味着：

1. `BOF family` 当前不是“所有 quality split 都无效”
2. 但只有一支分支被允许作为正式 retained 主位进入 `N1.12`
3. 这支 retained branch 不是短窗快读里曾出现过的 `BOF_PINBAR_EXPRESSION`，而是在三年长窗上改写成了 `BOF_KEYLEVEL_PINBAR`

---

## 4. 四支 quality branches 的正式读数

在 `2023-01-03` 到 `2026-02-24` 的统一长窗口上，当前 formal summary 固定为：

| Label | Trade Count | EV | PF | MDD | Participation | Incremental Buys vs Control |
|---|---:|---:|---:|---:|---:|---:|
| `BOF_CONTROL` | `277` | `0.01609` | `2.61207` | `0.13267` | `0.80523` | `0` |
| `BOF_KEYLEVEL_STRICT` | `56` | `0.01838` | `2.01253` | `0.09739` | `0.96552` | `14` |
| `BOF_PINBAR_EXPRESSION` | `96` | `-0.00425` | `1.95520` | `0.15114` | `0.96970` | `27` |
| `BOF_KEYLEVEL_PINBAR` | `21` | `0.03355` | `1.91808` | `0.02685` | `1.00000` | `6` |

当前读数说明得很清楚：

1. `BOF_PINBAR_EXPRESSION` 在三年长窗上已经失去正向 edge，因此不能继续作为 retained 主位
2. `BOF_KEYLEVEL_STRICT` 虽然仍保持正 `EV` 且回撤优于 control，但提升维度与 retained 强度都不如交集分支
3. `BOF_KEYLEVEL_PINBAR` 以更高 `EV` 与显著更低 `MDD` 成为本轮 retained 主位

---

## 5. 为什么 retained branch 固定为 `BOF_KEYLEVEL_PINBAR`

### 5.1 它同时满足正 edge、样本密度和 control 改进门槛

当前 scorecard 对 retained candidate 的判定门槛要求：

1. `expected_value > 0`
2. `profit_factor >= 1.0`
3. 样本量或参与率通过最低继承门槛
4. 相对 `BOF_CONTROL` 至少改善两项核心维度

`BOF_KEYLEVEL_PINBAR` 当前满足：

1. `positive_edge_ok = True`
2. `sample_density_ok = True`
3. `ev_improves_control = True`
4. `mdd_improves_control = True`
5. `improvement_count = 2`

### 5.2 它的 retained 身份来自“更纯的交集子集”，不是来自暴力扩大样本

当前 retained 分支的 selected trace summary 固定为：

1. `selected_count = 21`
2. `keylevel_pass_ratio = 1.0`
3. `pinbar_pass_ratio = 1.0`
4. `avg_keylevel_proxy_score = 83.70629`
5. `avg_pinbar_proxy_score = 85.81697`

这说明：

`BOF_KEYLEVEL_PINBAR` 不是通过放宽 detector 获得 retained 身份，而是通过“关键位更强 + rejection 表达更清楚”的交集子集获得 retained。`

### 5.3 retained 只代表“进入 N1.12”，不代表已经可升格

这里必须明确：

1. `N1.11` 只负责在 `BOF family` 内部选 retained branch
2. retained 不等于 `N2 eligible`
3. retained 只等于：
   - 允许进入 `N1.12`
   - 接受进一步稳定性与 purity 审核

---

## 6. 正式结论

当前 `N1.11` 的正式结论固定为：

1. `BOF family` 当前确实存在比 `BOF_CONTROL` 更值得继续审的 quality branch
2. 这支 retained branch 固定为 `BOF_KEYLEVEL_PINBAR`
3. `BOF_KEYLEVEL_STRICT` 保留为次级正向候选，但不成为 retained 主位
4. `BOF_PINBAR_EXPRESSION` 在三年长窗上正式 `no-go`
5. `Normandy` 下一步应进入：
   - `N1.12 / BOF family stability or no-go`

换句话说：

`N1.11` 已经把问题回答成了：BOF family 里不是完全没有质量分支，但真正值得继续推进的 retained 主位只有 `BOF_KEYLEVEL_PINBAR`。`

---

## 7. 后续动作

对 `BOF family` 而言，当前后续动作固定为：

1. 只对 `BOF_KEYLEVEL_PINBAR` 打开 `N1.12`
2. 不重新把 `FB / SB / Tachibana` 拉回本卡
3. 不把 `BOF_KEYLEVEL_STRICT` 误读成第二条平行 retained 主位

对 `Normandy` 主队列而言，当前下一步固定为：

1. `N1.12 / BOF family stability or no-go`
2. 若 retained branch 未通过稳定性审核，则 `N2` 继续锁住

---

## 8. 一句话结论

`N1.11` 已经用三年长窗把 `BOF` quality split 真正读成 formal retained 结论：`BOF_KEYLEVEL_PINBAR` 是当前唯一值得继续推进到 `N1.12` 的 retained branch，而 `BOF_PINBAR_EXPRESSION` 已经正式退场。`
