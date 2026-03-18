# Phase 9B Readiness Note / context_trend_direction_before

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 这份 note 解决什么

这份 note 只解决 `17.5` 开工前还没过的两道门：

1. `它是不是 wave_role 的换名复跑`
2. `GX8 对当前这轮 isolated validation 到底是不是阻塞`

---

## 2. 字段对齐先写清

`17.5` 卡面沿用的是 Gene ledger 侧名字：

`context_trend_direction_before`

但当前主线 runtime 真正能消费的 snapshot 字段是：

`current_context_trend_direction`

因此这一轮如果要做正式 isolated validation，必须诚实写成：

`用 runtime snapshot 字段 current_context_trend_direction，去验证 ledger 侧 parent-context direction 语义是否值得进入主线。`

换句话说：

1. `context_trend_direction_before` 是 ledger 语义名
2. `current_context_trend_direction` 是 runtime 验证入口名
3. 本轮两者不是两个东西，而是一条语义在 ledger / snapshot 两层的不同落盘名字

---

## 3. 它是不是 wave_role 的换名复跑

不是。

基于 `17.4 / reversal_state` 正式工作库

`G:\EmotionQuant-temp\backtest\phase9-reversal-validation-20260319.duckdb`

在正式窗口 `2026-01-05 ~ 2026-02-24` 下，`16` 个 formal signals 的结构分布是：

1. `current_wave_role = COUNTERTREND`：`12`
2. `current_context_trend_direction = DOWN`：`6`
3. 二者重叠：`2`
4. `context_down_without_countertrend = 4`
5. `countertrend_without_context_down = 10`

对应的明细结构是：

1. `DOWN + COUNTERTREND + context UP`：`10`
2. `DOWN + MAINSTREAM + context DOWN`：`4`
3. `UP + COUNTERTREND + context DOWN`：`2`

这说明：

1. `wave_role` 关注的是“当前 wave 相对父趋势是主流还是逆流”
2. `current_context_trend_direction` 关注的是“父趋势方向本身是什么”
3. 在当前正式窗口里，这两个字段并没有收敛成同一把尺

最关键的一点是：

`current_context_trend_direction = DOWN` 还抓到了 `4` 个 `MAINSTREAM` 信号，说明它不是简单复读 `COUNTERTREND`。`

所以当前正式判断应写成：

`17.5 不是 wave_role 的换名复跑。`

---

## 4. GX8 对这轮是不是阻塞

对未来 package closeout 来说，`GX8` 仍然是阻塞项。  
对当前这轮 `17.5` 的 isolated proxy validation 来说，可以先写成：

`non-blocking`

原因不是 `GX8` 不重要，而是：

1. `GX8` 解决的是 `short / intermediate / long` 三层趋势并存语义
2. 当前 `17.5` 不声称自己在验证未来三层 hierarchy
3. 当前 `17.5` 只验证现有 runtime snapshot 里已经真实落盘的：
   `current_context_trend_direction`
4. 这条字段当前本来就是 `INTERMEDIATE` 父趋势 proxy

因此当前最诚实的裁法是：

1. `GX8` 继续阻塞 `Phase 9` 包级 closeout
2. `GX8` 继续阻塞未来任何“三层正式语义”的 promotion closeout
3. 但 `GX8` 不阻塞当前这轮对 `INTERMEDIATE parent-context proxy` 的 isolated validation

一句话说：

`GX8 对 package closeout 仍是 blocking；对 17.5 这轮 proxy 字段 isolated validation，可先裁成 non-blocking。`

---

## 5. Readiness ruling

因此这份 readiness note 的正式结论是：

1. `17.5` 已通过 redundancy gate
2. `GX8` 对本轮可裁为 `non-blocking for isolated proxy validation only`
3. `17.5` 现在可以从 `Planned` 切到 `Active`

但这份 note **没有**声称：

1. `GX8` 已完成
2. `GX8` 对 `Phase 9C / 9D` 已不再构成阻塞
3. `context_trend_direction_before` 已经赢下 isolated round

它只声称：

`17.5 现在具备诚实开工的资格。`
