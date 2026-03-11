# Normandy N1 BOF 结论记录

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1-A`  
**对象**：`PAS raw alpha provenance 首轮 BOF 结论固定`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1-A` 的首轮 `BOF` 结论固定下来。

本记录只回答当前系统里的一个问题：

`在 A 股日线 + T+1 Open + v0_01_dtt_pattern_only 的当前执行语义下，BOF 是否仍然应该作为 PAS raw alpha provenance 的固定对照与当前有效 baseline。`

本文不改写：

1. `blueprint/` 主线 SoT
2. `PAS` 五形态 taxonomy
3. `Normandy` 后续可能继续展开的 `exit damage decomposition`

---

## 2. 参考依据

### 2.1 来源语义参考

1. `docs/Strategy/PAS/lance-beggs-ytc-analysis.md`
2. `docs/Strategy/PAS/xu-jiachong-naked-kline-analysis.md`

这两份参考在当前问题上的共同点很明确：

1. `BOF` 的本质不是“价格跌回去”本身，而是一次带有位置语义的 `breakout failure`
2. 关键行为链是：
   - 接近关键位置
   - 尝试突破
   - 突破无法延续
   - 回到原区间
   - 错误方向被套并触发反向加速
3. `Pin Bar` 在当前仓库口径里更适合作为 `BOF quality / explanation` 的补充线索，而不是独立替代 `BOF` 的正式执行定义

参考文档给当前系统的直接启发也一致：

1. `YTC` 把 `BOF` 视为五形态之一，且明确适合作为先落地的核心形态
2. `许佳冲` 文档把 `BOF / Pin Bar` 放回 A 股语境，强化了“假突破失败 -> 反向加速”这一行为解释
3. 两份文档都不直接定义当前代码中的 formal 参数、阈值和执行契约

### 2.2 实证证据参考

1. `normandy/03-execution/evidence/normandy_pas_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t165527__pas_alpha_matrix.json`
2. `normandy/03-execution/evidence/normandy_pas_alpha_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t194336__pas_alpha_digest.json`

首轮矩阵固定比较：

1. `BOF`
2. `BPB`
3. `PB`
4. `TST`
5. `CPB`
6. `YTC5_ANY`

---

## 3. 来源层结论

结合 `YTC` 与 `许佳冲` 两份参考，当前系统对 `BOF` 的来源层结论固定为：

1. `BOF` 是一个结构清晰、行为链完整、位置语义明确的正式 PAS 形态，不是偶然的单根 K 线标签
2. `BOF` 的交易逻辑核心是：
   - 突破尝试看起来成立
   - 但无法延续
   - 错误方向仓位被迫退出
   - 由此带来反向运动加速
3. `BOF` 适合作为当前系统最先落地、最先验证的最小可交易形态
4. `Pin Bar` 对当前 `BOF` 有解释价值，但在本轮结论中仍只属于 `quality / reference` 语义，不升格为独立 formal pattern

因此，若只看来源语义，当前主线先用 `BOF` 作为 PAS 最早在线形态，来源上是自洽的。

---

## 4. N1-A 长窗证据结论

在 `2023-01-03` 到 `2026-02-24` 的统一长窗口上，`BOF` 是首轮矩阵中唯一保持正 `EV` 的单形态：

| Label | Trade Count | EV | PF | MDD | Participation |
|---|---:|---:|---:|---:|---:|
| `BOF` | 277 | 0.01609 | 2.6121 | 0.13267 | 0.80523 |
| `YTC5_ANY` | 608 | -0.00460 | 2.2144 | 0.54535 | 0.10646 |
| `PB` | 409 | -0.00712 | 2.2042 | 0.41512 | 0.39670 |
| `TST` | 378 | -0.00924 | 2.0978 | 0.38643 | 0.43801 |
| `CPB` | 477 | -0.01160 | 2.1515 | 0.52322 | 0.12997 |
| `BPB` | 27 | -0.09379 | 0.1411 | 0.21350 | 1.00000 |

当前 digest 的正式判断为：

1. `provenance_leader = YTC5_ANY`
2. `n2_candidates = []`
3. 当前没有非 `BOF` shape 同时满足 `entry edge` 与样本密度门槛

这里需要明确区分：

1. `YTC5_ANY` 是观察领先者，不等于当前可升格的 raw alpha baseline
2. `BOF` 是当前唯一同时满足：
   - 正 `EV`
   - 较高 `PF`
   - 相对更低 `MDD`
   - 足够样本量
   - 更稳的参与率口径
3. 因此首轮矩阵没有推翻 `BOF`，反而把 `BOF` 重新钉实为当前系统中的有效对照

---

## 5. 正式结论

结合两份来源文档与 `N1-A` 的长窗实证，当前 `BOF` 结论固定为：

1. `BOF` 继续作为当前系统下最可信的 `PAS raw alpha baseline`
2. `BOF` 继续作为 `Normandy` 进入 `N2` 之前的固定对照，不撤销、不替换
3. `PB / TST / CPB / BPB / YTC5_ANY` 在本轮证据中都未形成“可直接推翻 BOF”的条件
4. `YTC5_ANY` 仅保留为后续观察对象，不得因为 trade_count 更高就直接升格为新 baseline
5. `Pin Bar` 继续保留在 `BOF quality / explanation` 层，不在本结论中扩写成新的正式执行口径

换句话说：

`BOF` 在理论来源上成立，在当前系统长窗证据上也仍然成立；因此它不是“历史残留默认值”，而是当前仍被证据支持的有效 baseline。

---

## 6. 边界与后续动作

本记录同时固定以下边界：

1. 这不是在宣告 `BOF` 永远优于所有 `PAS` 形态
2. 这只是当前 `A 股日线 + T+1 Open + pattern_only` 语义下的系统结论
3. `Normandy` 后续若继续推进，应优先围绕：
   - 为什么 `YTC5_ANY` 交易数更高但 `EV` 反转
   - 非 `BOF` 形态的损伤主要来自 entry、exit 还是 execution
4. 在新证据出现前，`BOF` 保持为 `N2` 前固定对照，不能跳过这条基线直接宣布新 shape 升格

---

## 7. 一句话结论

结合 `YTC` 与 `许佳冲` 参考，`BOF` 在来源上代表的是“假突破失败后由 trapped traders 退出驱动的反向机会”；结合 `Normandy / N1-A` 三年长窗证据，`BOF` 仍是当前系统里唯一被证据确认的正向 `PAS raw alpha baseline`。
