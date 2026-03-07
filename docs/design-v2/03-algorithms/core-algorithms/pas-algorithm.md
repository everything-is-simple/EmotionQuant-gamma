# PAS-trigger 算法设计（当前执行版）

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变当前 DTT 主线边界的前提下，对 PAS-trigger 的 detector 架构、BOF 口径与扩展计划做受控修订。`  
**上游文档**: `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md`  
**创建日期**: `2026-03-06`  
**最后更新**: `2026-03-08`  
**对应模块**: `src/strategy/pattern_base.py`, `src/strategy/pas_bof.py`, `src/strategy/registry.py`, `src/strategy/strategy.py`  
**理论来源**: `docs/Strategy/PAS/`

---

## 1. 当前定位

当前 `gamma` 主线里实现的，不是 `PAS-full`，而是：

`PAS-trigger`。

这里的 `PAS-trigger` 指的是：

- 从原始 `Price Action` 交易体系中抽取出的“形态触发器子集”
- 当前只承担 `BOF` 触发职责
- 不承接完整的交易管理、目标位、失败处理与多形态生态

因此必须区分两层：

1. **PAS-full**
   - 位于 `docs/Strategy/PAS/`
   - 对应 Lance Beggs / Volman / 许佳冲 等原始理论体系
   - 包含形态、结构、入场、止损、目标位、失败处理、纪律与资金管理

2. **PAS-trigger**
   - 位于当前主线代码和本文件
   - 对应当前系统实际可运行的触发器子集
   - 当前仅在线 `BOF`

这两者不是一回事，不能再混写。

---

## 2. 与原始 PAS 的关系

### 2.1 当前保留下来的部分

当前 `PAS-trigger` 直接继承了原始 PAS 中最核心的一层：

- 形态识别
- 结构优先
- 一形态一 detector
- 触发后再进入后续执行链路

### 2.2 当前被裁剪掉的部分

当前主线没有完整承接以下原始 PAS 内容：

- `BPB / TST / PB / CPB` 的在线形态生态
- 形态质量评分
- 目标位与止损位的正式执行契约
- 失败形态处理
- 完整的 Price Action 交易管理

因此，当前系统不能再被表述为“已经实现了 PAS”，更准确的说法必须是：

`当前主线实现的是 PAS-trigger 当前执行版。`

---

## 3. 当前主线职责

在 `v0.01-plus` 当前主线中，`PAS-trigger` 只回答一个问题：

`候选池中的这只股票，今天是否触发了可执行的 BOF 形态。`

当前它不回答：

- 这只股票最终排第几
- 今天能开多大仓位
- 止损与目标位怎么管理
- 失败后是否反手

这些职责分别交给：

- `IRS`：横截面排序增强
- `MSS`：市场级控仓位
- `Broker / Risk`：执行截断与仓位约束

---

## 4. 当前算法骨架

### 4.1 detector 模式

每个形态一个 detector，统一接口：

```python
class PatternDetector(ABC):
    name: str

    @abstractmethod
    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        ...
```

这保证了：

- 单形态可独立回测
- 单形态可独立开关
- 单形态可单独补测试
- 后续形态扩展不破坏当前骨架

### 4.2 registry 装配

`registry.py` 当前只负责：

- 注册 detector
- 校验启用模式
- 返回当前活跃 detector 列表

当前正式在线 detector 只有：

- `bof`

### 4.3 strategy 汇总

`strategy.py` 当前只负责：

1. 为候选票批量准备历史窗口
2. 调用活跃 detector
3. 合并 detector 结果
4. 在 `DTT` 路径下对接 sidecar 排序链路

---

## 5. 当前 BOF 定义

当前 `BOF` 的正式触发条件仍是：

1. `low < lower_bound * (1 - break_pct)`
2. `close >= lower_bound`
3. `close_pos >= 0.6`
4. `volume >= volume_ma20 * volume_mult`

满足即在 `T` 日收盘后生成最小 `BUY Signal`。

当前 `BOF` 输出：

- `signal_id`
- `code`
- `signal_date`
- `action = BUY`
- `pattern = bof`
- `reason_code = PAS_BOF`
- `strength`

`strength` 在当前主线下可以进一步抬升为：

- `bof_strength`

供 `DTT` 排序解释使用。

---

## 6. 当前边界

### 6.1 当前正式支持

- `BOF` 单形态
- `ANY` 组合模式
- `detector -> formal signal -> DTT sidecar` 这条链路

### 6.2 当前不支持

- `BPB / TST / PB / CPB` 在线运行
- 形态质量评分进入主线
- 止损/目标位作为正式执行契约
- 失败形态处理
- detector 直接消费 `IRS / MSS`

---

## 7. 当前设计资产

即使当前只实现了 `PAS-trigger`，它仍然有两块重要资产：

1. `detector / registry / strategy` 的骨架清楚
2. 它已经和 `DTT sidecar` 排序链路打通

这意味着后续恢复原始 PAS 的更多内容时，不需要推倒重来，而是沿着当前骨架逐步把缺失层补回去。

---

## 8. 恢复路径

当前 `PAS` 不该永远停留在 trigger 子集。

下一步恢复路径已经单独立项：

- `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md`

恢复分三批：

1. **形态生态恢复**
   - `BPB / TST / PB / CPB`
2. **形态质量评分恢复**
   - 结构清晰度 / 量能确认 / 位置优势 / 失败风险
3. **交易管理参考恢复**
   - 止损 / 目标位 / 风险收益比 / 失败处理

---

## 9. 权威结论

当前正式结论必须写清楚：

- `docs/Strategy/PAS/` 对应 `PAS-full`
- 当前主线代码实现的是 `PAS-trigger`
- 当前 `PAS-trigger` 只在线 `BOF`
- 后续要恢复原始 PAS 的更多内容，但必须沿着当前骨架分批推进

---

## 10. 参考文献

1. `docs/Strategy/PAS/lance-beggs-ytc-analysis.md`
2. `docs/Strategy/PAS/xu-jiachong-naked-kline-analysis.md`
3. `docs/Strategy/PAS/volman-ytc-mapping.md`
4. `docs/Strategy/PAS/tachibana-yoshimasa-analysis.md`
5. `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md`
