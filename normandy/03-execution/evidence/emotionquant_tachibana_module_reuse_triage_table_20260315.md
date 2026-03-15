# EmotionQuant-gamma 模块对立花验证复用分流表

**日期**: `2026-03-15`  
**范围**: `EmotionQuant-gamma -> Tachibana validation reuse triage`  
**结论口径**: `直接复用 / 改造后复用 / 退出立花主线`

---

## 1. 裁决原则

本文中的“废弃”不表示立即删除代码，而表示：

`退出立花主线，不再作为 Tachibana quantifiable system 的正式入口；仅保留为历史对照、局部参考或回归基线。`

判断标准只看 3 件事：

1. 是否已经能承载 `position-aware / leg-aware / state-transition-aware` 语义  
2. 是否能直接进入可验证、可回放、可比较的实验链路  
3. 是否会把立花误压成单一 `contrary alpha` 或单一 detector

---

## 2. 复用分流总表

| 模块 / 路径 | 当前判定 | 为什么 | 对立花验证中的角色 |
|---|---|---|---|
| `positioning/03-execution/` + `scripts/backtest/run_positioning_*` | `直接复用` | 已有 null-control / sizing / partial-exit 的成套实验战场、runner、digest、record | 作为 Tachibana 执行系统验证的主实验底座 |
| `src/backtest/partial_exit_null_control.py` | `直接复用` | 已经显式读取 `position_id / exit_leg_id / is_partial_exit`，并能比较 operating control vs floor control | 用来做“分腿退出是否成立”的首层 control matrix |
| `src/backtest/positioning_partial_exit_family.py` | `直接复用` | 已能批量比较 `25/75、33/67、50/50...` 的 ratio family，并输出 retained/watch 读数 | 用来验证立花式“轻首腿、重尾仓”是否有稳定优势 |
| `src/contracts.py` | `直接复用` | `position_id / exit_plan_id / exit_leg_id / PositionStateType` 已 formalize | 作为立花 `母单 / 腿 / 状态` 的身份层基座 |
| `src/report/reporter.py` | `直接复用` | `_pair_trades()` 已经按 `position_id` 做 position-aware 配对，并保留 `exit_leg_id / is_partial_exit` | 作为立花路径忠实度与 pair-level 绩效核对层 |
| `tests/unit/broker/test_broker.py` + `tests/patches/broker/test_broker_trace_semantics_regression.py` | `直接复用` | partial-exit leg、trace identity、position state 已有回归保护 | 作为后续改造不回退的护栏 |
| `scripts/ops/build_tachibana_tradebook_scaffold.py` + `scripts/ops/build_tachibana_replay_ledger.py` | `直接复用` | 已经是 Tachibana 研究专用脚手架 | 作为书中交易谱向结构化 ledger 过渡的入口 |
| `normandy/02-implementation-spec/10-tachibana-quantifiable-execution-system-spec-20260315.md` | `直接复用` | 当前唯一把立花定义为执行系统而非单 detector 的 SoT | 作为后续实现和验证的总契约 |
| `src/broker/broker.py` | `改造后复用` | 身份层、exit plan、多腿 SELL 已可用，但执行主线仍是 `BUY-only` 入场、A 股 long-only 约束 | 可复用其订单/腿/trace 机制；不能直接充当立花原书的 long-short 锁单回放引擎 |
| `src/backtest/engine.py` | `改造后复用` | 适合 A 股 BOF 主线回测，但不天然表达“锁单共存 / 试单休息 / 反向再出发” | 可作为日线推进器；需外接更强的 state machine |
| `src/backtest/normandy_tachibana_alpha.py` | `改造后复用` | 当前只把立花压成 `BOF_CONTROL vs TACHI_CROWD_FAILURE` 的二元 alpha 搜索 | 只保留为 `L1 opportunity context` 或历史对照，不再代表立花全貌 |
| `src/strategy/tachibana_detectors.py` | `改造后复用` | 当前 detector 只覆盖一类 `crowd failure reclaim` 形态 | 只可作为“机会触发候选”，不能再冒充立花执行法本体 |
| `scripts/backtest/run_normandy_tachibana_alpha_matrix.py` + `run_normandy_tachibana_alpha_digest.py` | `退出立花主线` | 仍然服务于旧 `contrary alpha search` 口径 | 仅保留为历史对照，不再作为当前立花研究入口 |
| `normandy/02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md` | `退出立花主线` | 口径已被 `10-...quantifiable-execution-system-spec` 取代 | 保留归档价值，不再作为当前 SoT |
| `normandy/03-execution/records/04-phase-n1-8-tachibana-contrary-alpha-record-20260312.md` | `退出立花主线` | 对应旧问题定义，不再是当前研究问题 | 仅保留历史证据链 |

---

## 3. 最重要的硬判断

### 3.1 当前最该依赖的主干

当前对立花最有用的主干不是：

`old tachibana detector -> alpha matrix`

而是：

`tradebook / replay ledger -> contracts -> partial-exit family -> positioning evidence`

也就是说，仓库里真正成熟的，不是“发现立花买点”，而是“验证分腿、母单、路径、退出语义”的能力。

### 3.2 当前最大的结构错位

`SignalActionType = Literal["BUY"]` 与 Broker 的 `BUY-only` 主线，决定了现有执行内核天然更接近：

`A 股长仓建仓 -> 分腿退出`

而不是：

`原书里的 long-short 锁单并存回放`

所以：

`不能把现有 Broker 直接等同于立花原书执行器。`

更正确的做法是：

1. 先用 `tradebook/replay ledger` 重建立花状态机  
2. 再把其中能迁回 A 股 BOF 主线的部分，映射到 `position_id / exit_leg_id / partial_exit family`

### 3.3 当前最值得保留的工程资产

当前最值得保留的不是旧 `TACHI_CROWD_FAILURE`，而是这 4 个工程资产：

1. `position-aware identity`
2. `partial-exit family replay`
3. `position-aware reporter pairing`
4. `record + evidence + digest` 的治理链路

---

## 4. 快速动作建议

如果目标是把立花方法变成可量化、可验证系统，当前最短路径固定为：

1. 继续扩充 `tradebook -> replay ledger -> state_transition`
2. 把书中 `试单 / 母单 / 锁单 / 解锁 / 全平休息` 落成规则候选表
3. 用 `positioning` 战场去验证哪些规则能迁回 A 股 BOF 主线
4. 明确把旧 `tachibana alpha` 口径降级为历史对照

---

## 5. 一句话结论

`EmotionQuant-gamma` 里真正可用来做立花验证的，是一套已经成型的仓位与退出实验基础设施；旧 tachibana detector 不是主引擎，只是历史残留的窄入口。
