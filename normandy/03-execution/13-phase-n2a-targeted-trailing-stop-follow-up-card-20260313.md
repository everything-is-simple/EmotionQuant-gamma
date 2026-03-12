# Phase N2A BOF Control Targeted Trailing-Stop Follow-Up Card

**状态**: `Active`  
**日期**: `2026-03-13`  
**对象**: `N2 baseline lane targeted trailing-stop follow-up around BOF_CONTROL`

---

## 1. 定位

这张卡是 `Normandy / N2 baseline lane` 的直接 follow-up。

它不是：

1. 重新打开 `BOF quality branch promotion`
2. 借机重开 `Tachibana / FB / SB / PB / TST / CPB` 大混战
3. 把 `STOP_ONLY` 的 uplift 直接翻译成“主线立刻取消 trailing-stop”

它只回答：

`在 BOF_CONTROL 已经被 formal readout 证明“不是买错、也不是 execution friction 主导”的前提下，当前 trailing-stop 到底在哪些 trade path 上过早砍掉了 fat-tail winners，这种伤害是结构性的，还是只是一小撮极端样本。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/01-alpha-provenance-and-exit-decomposition-spec-20260311.md`
3. `normandy/03-execution/12-phase-n2-bof-control-baseline-exit-decomposition-card-20260313.md`
4. `normandy/03-execution/records/12-phase-n2-bof-control-baseline-exit-decomposition-record-20260313.md`
5. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

---

## 3. 当前前置结论

`N2 baseline lane` 第一轮 formal readout 已经固定：

1. `BOF_CONTROL` 不是 `买错`
2. `execution friction` 当前不是主因
3. `exit damage` 当前确实存在，但读数是 `mixed / concentrated damage`
4. 最可疑路径是：`trailing-stop` 对少数 fat-tail winners 的过早收割
5. `promotion lane` 继续锁住

因此这张 follow-up card 的任务不是重判 baseline，而是继续把 `trailing-stop damage` 读细。

---

## 4. 固定研究对象

本卡固定只围绕：

1. `BOF_CONTROL` 已成交 entry set
2. 当前 `broker-frozen` control exit
3. 与 `trailing-stop` 直接相关的受控变体

硬约束：

1. 不重开 `BOF_KEYLEVEL_PINBAR / BOF_KEYLEVEL_STRICT / BOF_PINBAR_EXPRESSION`
2. 不把 `FB / SB / Tachibana / Volman deferred queue` 拉回主队列
3. 不回头改 entry layer
4. 不把本卡结果直接迁回主线默认参数
5. 不因为本卡而自动放行 `promotion lane`

---

## 5. 当前只允许研究的问题

本卡当前只允许回答下面这些问题：

1. `TRAILING_STOP` 触发的 trade 里，哪些 actually 后来走成了大赢家
2. 当前 trailing-stop 的伤害是集中在：
   - 早期启动
   - 过紧阈值
   - 单次高波动震出
   - 长趋势持仓中的中段回撤
3. `STOP_ONLY` 的巨大 uplift，到底来自：
   - 少数极端 fat-tail winners
   - 还是一整类可重复的 trend-carry path
4. 当前 trailing-stop 的收益保护作用，到底抵消了多少后续亏损放大

换句话说：

`这张卡要把“trailing-stop 很可疑”进一步拆成可解释的 path family，而不是只停留在总表 uplift。`

---

## 6. 任务拆解

### N2A-1 Trailing-Stop Path Segmentation

目标：

1. 只抽取 `CONTROL_REALIZED` 中 `exit_reason = TRAILING_STOP` 的 trade 集
2. 对它们做 path segmentation：
   - `fat-tail winner cut`
   - `legitimate protection`
   - `late trend exhaustion`
   - `ambiguous / mixed`
3. 形成至少一份可复核的 case table

### N2A-2 Controlled Trailing Variants

目标：

1. 只围绕 trailing-stop 维度做受控变体
2. 不取消 hard stop
3. 不改 entry set
4. 至少比较：
   - `current trailing stop`
   - `looser trailing stop`
   - `delayed trailing activation`（若实现成本可控）
   - `profit-gated trailing activation`（若实现成本可控）

### N2A-3 Formal Readout

目标：

1. 正式回答 trailing-stop 的伤害更像：
   - `small cluster of outlier truncation`
   - `repeatable trend-premature-exit pattern`
   - `not robust enough to act on`
2. 给出后续治理动作：
   - 继续深挖 trailing-stop semantics
   - 或把 `N2 baseline lane` 暂时停在当前 mixed verdict
3. 明确写死：这仍然不会自动解锁 `promotion lane`

---

## 7. 建议证据

本卡建议至少输出：

1. `trailing_stop_case_table.json`
2. `trailing_stop_path_report.json`
3. `targeted_trailing_stop_digest.json`

如需新增脚本，建议命名为：

1. `scripts/backtest/run_normandy_bof_control_trailing_stop_followup.py`
2. `scripts/backtest/run_normandy_bof_control_trailing_stop_digest.py`

---

## 8. 出场条件

本卡只有在以下条件全部满足时才允许出场：

1. 已把 `TRAILING_STOP` trade 子集从 control baseline 中单独剥离出来
2. 已对主要高 uplift / 高 damage 样本形成 case 解释
3. 已正式回答 trailing-stop damage 更像结构性问题，还是 outlier cluster
4. 已写清这不会自动改写主线默认 exit
5. 已写清这不会自动解锁 `promotion lane`

---

## 9. 当前一句话任务

`不要把 STOP_ONLY 的 uplift 当成口号；把 CONTROL_REALIZED 里那些被 trailing-stop 提前砍掉的大赢家路径逐笔拆开，读清这到底是结构性伤害，还是少数极端样本。`
