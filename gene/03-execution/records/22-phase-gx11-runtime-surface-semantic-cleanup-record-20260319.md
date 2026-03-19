# GX11 Record: 运行面语义清理
**状态**: `Completed`
**日期**: `2026-03-19`

---

## 1. 记录目的

这份 record 只记录四件事：

1. `GX11` 到底清掉了哪些运行面歧义
2. 哪些旧字段被保留为兼容层
3. 新增透明字段分别回答什么问题
4. 当前验证做到哪里

---

## 2. 本轮正式结论

### 2.1 `age_band` 已正式收口成 duration 展示别名

当前实现没有删除：

1. `current_wave_age_band`
2. `wave_age_band`

因为这两个字段已经进入了旧报表、旧 evidence 和条件层统计。

但本轮已新增：

1. `current_wave_age_band_basis`
2. `wave_age_band_basis`

并把它们固定写成：

`DURATION_BAND_ALIAS`

这意味着当前仓库已经正式写死：

`age_band` 不是独立新变量，而只是 `duration band` 的展示别名。`

### 2.2 canonical context 与 hierarchy context 的关系已显式化

当前旧字段：

1. `current_context_trend_level`
2. `current_context_trend_direction`

继续保留，避免静默改坏 `Phase 9` 已存在消费面。

但本轮额外新增：

1. `current_context_view_scope`
2. `current_context_view_level`
3. `current_context_parent_trend_level`
4. `current_context_parent_trend_direction`

当前正式口径因此写定为：

1. canonical row 是 `CANONICAL_INTERMEDIATE_VIEW`
2. `current_context_trend_level = INTERMEDIATE` 代表的是 canonical view level
3. canonical row 真正对应的父层上下文，应读 `current_context_parent_trend_level / direction`
4. 若要读显式 hierarchy，则继续优先读 `current_short_* / current_intermediate_* / current_long_*`

也就是说，当前 `current_context_trend_direction` 仍可继续服务旧 runtime guard，  
但它已经不再伪装成“完整无歧义的 hierarchy context 合同”。

### 2.3 `reversal_state` 现在不再是唯一可消费视图

当前保留：

`reversal_state`

但同时新增：

1. `reversal_state_family`
2. `reversal_state_is_confirmed_turn`
3. `reversal_state_is_two_b_watch`
4. `reversal_state_is_countertrend_watch`

当前正式口径写定为：

1. `reversal_state` 仍是压缩视图
2. 新消费方如果需要透明度，应直接读 family / flags
3. 旧消费方仍可继续按 `reversal_state == CONFIRMED_TURN_DOWN` 工作

这让系统现在可以直接回答：

1. 这是 confirmed turn 还是不是
2. 这是 2B watch 还是不是
3. 这是 countertrend watch 还是不是

而不再需要只靠字符串做反向猜测。

---

## 3. 本轮明确保留的兼容层

`GX11` 这轮刻意没有做下面这些破坏性动作：

1. 没有改 `current_wave_age_band` 的值
2. 没有改 `current_context_trend_direction` 的旧字段名
3. 没有改 `reversal_state` 的既有判定优先级
4. 没有回写或重跑 `Phase 9` 旧 evidence

当前策略不是：

`清理歧义 = 直接改旧字段`

而是：

`清理歧义 = 给旧字段补明示边界和透明 companion fields。`

---

## 4. 验证口径

本轮验证当前写定为：

1. `python -m py_compile src/selector/gene.py src/data/store.py tests/unit/selector/test_gene.py` 已通过
2. `tests/unit/selector/test_gene.py` 已新增 alias / context / reversal transparency 断言
3. 等价手工 smoke 已逐个执行 `5` 个 Gene 单测函数，结果全部通过
4. 正式 `pytest` 仍沿用本轮已有已知环境噪音：Windows 会话里的 `basetemp` 权限问题尚未单独清理

因此当前最诚实的结论是：

`GX11` 的合同清理已经完成，逻辑与兼容断言已站住，但正式 pytest 仍有独立环境噪音未处理。`

---

## 5. 下一步

当前固定进入：

[`../23-phase-gx12-post-remediation-gene-and-phase9-revalidation-card-20260319.md`](../23-phase-gx12-post-remediation-gene-and-phase9-revalidation-card-20260319.md)

也就是：

1. 重审 `G4 / G5 / G6` 旧证据还能不能直接保留
2. 重审 `Phase 9` 当前 isolated / freeze 口径是否要部分重算
3. 决定这轮整改只是数值漂移，还是已经触发治理翻案

---

## 6. 一句话收口

`GX11` 现在已经把 Gene 运行面从“旧字段能用但容易误读”推进到“旧字段保留兼容、透明字段同步暴露”的正式状态，因此后续重验证可以在更诚实的合同上进行。`
