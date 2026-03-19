# GX12 Record: 整改后 Gene 与 Phase 9 重验证裁决
**状态**: `Completed`
**日期**: `2026-03-19`

---

## 1. 记录目的

这份 record 只回答三件事：

1. `GX10 / GX11` 之后，哪些旧结论还能直接保留
2. 哪些旧结论必须重跑
3. `17.8 / 17.9` 现在应该怎么继续

---

## 2. 总裁决

当前正式裁决写定为：

1. `G4 / validation` = `rerun`
2. `G5 / mirror` = `rerun`
3. `G6 / conditioning` = `rerun`
4. `Phase 9B / duration_percentile` = `rerun`
5. `Phase 9B / context_trend_direction_before` = `keep`
6. `Phase 9B / reversal_state` = `keep`
7. `17.8 / duration sweep` = `pause legacy-surface attempt and reopen on remediated surface`
8. `17.9 / frozen combination replay` = `remain blocked until remediated 17.8 completes`

一句话压缩：

`当前不允许继续沿旧 duration surface 往下跑，但也不需要把 context / reversal 已有 isolated 结论全部推倒重来。`

---

## 3. 为什么 `G4 / G5 / G6` 必须 rerun

### 3.1 `G4`

`G4` 必须 rerun，原因不是因为主问题变了，而是因为寿命尺的参考基础变了。

`GX10` 这轮真实改动了：

1. `GENE_LOOKBACK_TRADE_DAYS`
2. `duration_percentile` 可见样本深度
3. `duration band / age band` 所依赖的历史窗口

因此：

`duration_percentile = PRIMARY_RULER`

这个结论的方向可以暂时保留为高可信候选，  
但它对应的数值、排序强度和验证表格不应继续假装原样不动。

所以 `G4` 的正式裁决只能是：

`rerun, not auto-revoke`

### 3.2 `G5`

`G5` 必须 rerun，原因是镜像层会直接消费 Gene snapshot 的主尺读数与排序。

当前 `duration_percentile` 的样本深度已经变了，`G5` 的：

1. `primary_ruler_rank`
2. `mirror_gene_rank`
3. 市场/行业镜像排序

都可能跟着发生数值漂移。

所以 `G5` 当前应读成：

`direction likely still valid, but evidence table must be refreshed`

### 3.3 `G6`

`G6` 也必须 rerun。

原因不是 `conditioning` 自己被重写了，而是它会消费：

1. `current_wave_age_band`
2. `current_wave_magnitude_band`
3. `latest_confirmed_turn_type`
4. `latest_two_b_confirm_type`

其中 `current_wave_age_band` 虽然在 `GX11` 被明示为 `duration` 展示别名，  
但它的实际 band 仍然受 `GX10` 的更深历史窗口影响。

所以 `G6` 不能继续假装旧条件层统计完全不动。

---

## 4. 为什么 `Phase 9B` 不是全部重开

### 4.1 `duration_percentile`

`Phase 9B / duration_percentile` 必须 rerun。

这不是可选项，因为 `17.8` 本来就要继续沿 duration 轴往下做书义寿命分布重跑。  
如果底层 duration surface 已经变了，却还让 `17.8` 沿旧 surface 开跑，就是治理漏洞。

因此当前正式写定：

`old isolated duration result stays as historical evidence, but all forward duration work must reopen on the remediated surface`

### 4.2 `context_trend_direction_before`

`Phase 9B / context_trend_direction_before` 当前可以 `keep`。

原因是：

1. `GX11` 没有改 `current_context_trend_direction` 的旧值
2. 新增的是透明 companion fields，而不是改旧 proxy 的输出
3. 当前 isolated rule 本来就是窄负向 guard：
   `block when current_context_trend_direction == DOWN`

所以它当前最诚实的裁决是：

`keep legacy isolated conclusion, but continue to label it as proxy`

### 4.3 `reversal_state`

`Phase 9B / reversal_state` 当前也可以 `keep`。

原因是：

1. `GX11` 没有改 `reversal_state` 的既有压缩值
2. 没有改它的判定优先级
3. 新增的只是 `family / flags` 透明层

而原本赢下 isolated validation 的，也只是：

`reversal_state == CONFIRMED_TURN_DOWN`

所以这条结论当前不需要因 `GX11` 自动推翻。

---

## 5. `17.8 / 17.9` 当前应如何继续

### 5.1 `17.8`

`17.8` 当前不该继续沿“整改前 duration surface”往下跑。

因此正式裁决写定为：

1. 已经存在的 `p95` formal round 与 `p65` sensitivity reference 继续保留为历史记录
2. 任何新的 `p65 ~ p95` sweep，不得继续默认消费整改前 duration surface
3. 当前应读成：
   `pause current legacy-surface attempt and reopen on remediated duration surface`

### 5.2 `17.9`

`17.9` 当前继续保持阻塞。

原因不是 scope 变了，而是它对 duration 输入的依赖现在更严格了：

1. 不允许继续默认拿旧 `p95`
2. 不允许默认拿整改前 duration surface 的 sweep 结果
3. 只能消费整改后 `17.8` 明确写出的 narrowing result

因此当前最诚实的状态就是：

`blocked-by-remediated-17.8`

---

## 6. 对当前主线的正式口径

当前 `Phase 9` 应读成：

`keep legacy isolated context/reversal conclusions, but pause and reopen all duration-driven follow-up work on the remediated surface`

这比简单写成：

`continue on legacy proxy surface`

更诚实，也比一刀切写成：

`everything must rerun`

更精确。

---

## 7. 一句话收口

`GX12` 的正式结论不是“所有旧 evidence 都作废”，而是“duration 轴相关后续必须在整改后 surface 上重开，context/reversal 旧 isolated 结论可保留为 legacy keep”。`
