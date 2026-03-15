# Tachibana Execution Semantics Evidence Table

**文档版本**：`v0.01`  
**文档状态**：`Active`  
**日期**：`2026-03-15`  
**适用范围**：`Normandy / Tachibana doctrine evidence table`

---

| 页码 | 语义对象 | 证据归纳 | 对系统的约束 | 当前可量化对象 |
|---|---|---|---|---|
| `B0288` | 分批进入 | 书页直接把 `分批买进` 列为方法清单首项。 | 系统不能默认一次性建满仓。 | `buy_units`, `ladder_step`, `leg_id` |
| `B0288` | 分批出场 | 书页同样把 `分批出场` 列为方法核心。 | 退出逻辑必须支持多腿减仓，不是只有全平。 | `sell_units`, `partial_exit_flag`, `state_transition` |
| `B0288` | 锁单 | 方法总纲里明示 `利用锁单`。 | 数据契约必须允许 `多/空` 同时存在。 | `open_long_units`, `open_short_units`, `lock_state_flag` |
| `B0288` | 小张数 | 方法总纲里强调 `张数不多`。 | 这不是激进放大系统，而是低承诺试探系统。 | `probe_unit`, `max_step_units` |
| `B0288` | 全部出场休息 | 方法总纲把 `经常全部出场休息` 写成基础纪律。 | 系统必须有 `flat + rest` 状态，不能永远在市。 | `rest_state`, `full_exit_event`, `position_id` 边界 |
| `B0288` | 买进与放空并用 | 方法总纲明确 `利用买进和放空`。 | 不能把立花误解成单方向做多系统。 | `buy_units`, `sell_units`, `direction_state` |
| `B0293` | 三个月一次的全平休息 | 页内明确建议阶段性全部平仓休息。 | 休息不是情绪词，是制度化的重置动作。 | `rest_trigger`, `cooldown_window` |
| `B0293` | 分批平仓有缺点 | 页内指出自己常分次平仓，但这种方式可能拖泥带水。 | 分批退出不是自动更优，必须受治理。 | `max_exit_legs`, `exit_completion_window` |
| `B0294` | 全平后以新投资者身份重进 | 页内强调全部平仓后再以新身份回到市场。 | 一个 `position_id` 结束后，下一个必须重新编号。 | `position_id_before`, `position_id_after`, `reentry_flag` |
| `B0294` | 全平休息非常重要 | 页内把全平休息提升到高优先级纪律。 | 交易系统必须允许主动停手，不以持续在场为目标。 | `flat_reason`, `rest_reason` |
| `B0294` | 锁单是测试性反向单 | 页内明确说自己的锁单带有测试单性质。 | 锁单不是纯对冲术语，而是试探机制的一部分。 | `probe_leg_flag`, `lock_state_flag`, `state_transition` |
| `B0295` | 锁单维持母单 | 页内说明锁单帮助维持母单与行情探索。 | `母单` 必须是正式对象，不能只留在文字里。 | `mother_position_flag`, `position_core_units` |
| `B0295` | 失败时也用锁单 | 页内提到失手时也用锁单。 | 错误管理不是单纯止损，还包括状态转换。 | `failure_transition`, `lock_after_failure_flag` |
| `B0295` | 张数要少 | 页内再次强调平时单量不要多。 | 仓位研究重点应是节律，不是杠杆。 | `base_unit`, `unit_growth_rule` |
| `B0295` | 买进和放空二选一更好 | 页内倾向一次专注一种方向。 | 方向切换需要明确边界，不能同周期乱切。 | `direction_mode`, `reverse_transition` |
| `B0304` | 100 股试验性多次摊平 | 页内说明 `1976-10` 到 `1976-12` 有试验性多次摊平。 | 这几个月要被标成试验段，不能与常规段混算。 | `regime_tag=experimental_100_share` |
| `B0304` | 试验失败但带来新刺激 | 页内承认这段试验不成功。 | 负样本也要保留，不能只留成功样本。 | `experiment_outcome`, `failure_tag` |
| `B0304` | 次年恢复 1000 股后重新出发 | 页内说明后续会恢复原交易单位。 | 交易单位变化是制度变量，不是噪音。 | `lot_size_regime`, `unit_scale` |
| `B0305` | 三个成功秘诀 | 页末把方法压缩成三条：自己的方法、分批交易、全部平仓出场。 | 系统设计必须围绕这三条，不应被附属技巧牵着走。 | `method_identity`, `ladder_management`, `full_exit_policy` |

---

## 当前结论

这组方法页给出的不是零散鸡汤，而是一个明确的执行 doctrine：

1. `分批交易`
2. `锁单作为测试机制`
3. `母单维持`
4. `小张数`
5. `阶段性全平休息`

因此立花方法的最小系统核心，不是 entry detector，而是：

`probe -> mother -> ladder -> lock -> flat -> rest`
