# G6 记录: BOF / PB / CPB 条件层统计已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 本次实现内容

1. 将 `Store` schema 正式升级到 `v10`
2. 新增 `l3_gene_conditioning_eval` 作为第四战场条件层正式表
3. 新增 `compute_gene_conditioning(store, calc_date)`，直接从 `l2_stock_adj_daily` 重构：
   - `BOF`
   - `PB`
   - `CPB`
   三类 detector trigger 样本
4. 第一版 `G6` 不依赖主库当前并不完整的 `l3_signals / l4_orders / l4_trades`，而是显式改走“价格重构触发样本”口径
5. 将以下第四战场标签正式回灌到条件层：
   - `current_wave_direction`
   - `current_wave_age_band`
   - `current_wave_magnitude_band`
   - `latest_confirmed_turn_type`
   - `latest_two_b_confirm_type`
   - `streak_bucket`
6. 每个 pattern / 条件分组固定输出：
   - `sample_size`
   - `hit_rate`
   - `avg_forward_return_pct`
   - `median_forward_return_pct`
   - `avg_mae_pct`
   - `avg_mfe_pct`
   - `hit_rate_delta_vs_pattern_baseline`
   - `payoff_delta_vs_pattern_baseline`
   - `mae_delta_vs_pattern_baseline`
   - `mfe_delta_vs_pattern_baseline`
   - `edge_tag`

---

## 2. 主库真实读数

本次读取对象：

`G:\EmotionQuant_data\emotionquant.duckdb`

截至：

`2026-02-24`

主库 `G6` 结果：

1. `_meta_schema_version = 10`
2. `compute_gene_conditioning()` 本轮真实写入：`64` 行
3. 三类 baseline 样本量分别为：
   - `bof = 15107`
   - `cpb = 16814`
   - `pb = 19713`

三类 baseline 读数：

1. `bof`
   - `hit_rate = 0.582776`
   - `avg_forward_return_pct = 3.369605`
   - `median_forward_return_pct = 2.167043`
   - `avg_mae_pct = 7.311051`
   - `avg_mfe_pct = 12.961569`
2. `cpb`
   - `hit_rate = 0.458071`
   - `avg_forward_return_pct = 0.933428`
   - `median_forward_return_pct = -0.578283`
   - `avg_mae_pct = 5.256747`
   - `avg_mfe_pct = 9.456609`
3. `pb`
   - `hit_rate = 0.443870`
   - `avg_forward_return_pct = 0.337060`
   - `median_forward_return_pct = -1.020408`
   - `avg_mae_pct = 7.218192`
   - `avg_mfe_pct = 9.811756`

当前主库最有代表性的 `BETTER` 条件层：

1. `bof / current_wave_direction = DOWN`
   - `sample_size = 14212`
   - `hit_rate_delta = +0.012144`
   - `payoff_delta = +0.338385`
   - `mae_delta = -0.062408`
   - `mfe_delta = +0.434213`
2. `bof / streak_bucket = UP_1`
   - `sample_size = 9587`
   - `hit_rate_delta = +0.025235`
   - `payoff_delta = +1.311795`
   - `mae_delta = -0.219569`
   - `mfe_delta = +1.782785`
3. `pb / current_wave_direction = DOWN`
   - `sample_size = 3460`
   - `hit_rate_delta = +0.027518`
   - `payoff_delta = +0.552088`
   - `mae_delta = -0.381368`
   - `mfe_delta = +0.767690`
4. `pb / current_wave_age_band = NORMAL`
   - `sample_size = 3795`
   - `hit_rate_delta = +0.027804`
   - `payoff_delta = +0.631695`
   - `mae_delta = -0.496224`
   - `mfe_delta = +0.224595`
5. `cpb / streak_bucket = UP_4P`
   - `sample_size = 4111`
   - `hit_rate_delta = +0.031348`
   - `payoff_delta = +0.627361`
   - `mae_delta = -0.540889`
   - `mfe_delta = +0.683119`
6. `cpb / latest_confirmed_turn_type = NONE`
   - `sample_size = 8709`
   - `payoff_delta = +0.200818`
7. `cpb / current_wave_age_band = UNSCALED`
   - `sample_size = 8334`
   - `payoff_delta = +0.203999`

当前主库最有代表性的 `WORSE` 条件层：

1. `bof / current_wave_direction = UP`
   - `sample_size = 895`
   - `hit_rate_delta = -0.192832`
   - `payoff_delta = -5.373324`
2. `bof / streak_bucket = DOWN_1`
   - `sample_size = 1001`
   - `payoff_delta = -4.086828`
3. `cpb / current_wave_age_band = EXTREME`
   - `sample_size = 2227`
   - `payoff_delta = -0.989880`
4. `cpb / current_wave_magnitude_band = EXTREME`
   - `sample_size = 1469`
   - `payoff_delta = -1.488402`
5. `cpb / latest_two_b_confirm_type = 2B_TOP`
   - `sample_size = 4585`
   - `payoff_delta = -0.488553`
6. `pb / current_wave_direction = UP`
   - `sample_size = 16253`
   - `payoff_delta = -0.117531`

---

## 3. 第一版 G6 结论

### 3.1 `BOF` 的 baseline 最强，但更像“下跌波里的第一脚反抽”

截至 `2026-02-24` 的主库样本里，`BOF` 是三类 pattern 里 baseline 最强的一类。  
但它最好的环境不是“已经在顺风主升里继续追”，而是：

1. `current_wave_direction = DOWN`
2. `streak_bucket = UP_1`

这说明当前 `BOF` 更像“下跌大波段中的第一脚向上修复/反抽”，而不是“顺主升继续追击”。  
相反，若当前已经处于 `UP` 背景，或者短期仍在 `DOWN_1 / FLAT`，读数会明显劣化。

### 3.2 `PB` 不是无脑回调就能打，只有落进明确历史尺后才略有改善

`PB` 的 baseline 是三类里最弱的。  
第一版主库结果里，`PB` 只在以下环境出现温和改善：

1. `current_wave_direction = DOWN`
2. `current_wave_age_band = NORMAL`
3. `current_wave_age_band = EXTREME`

这说明 `PB` 当前并不支持“只要像 pullback 就值得打”。  
它更像需要先知道这只票已经落在某个可识别的历史尺位置里，再去看 pullback 是否值得接。  
若处于 `UP` 背景，主库结果反而更差。

### 3.3 `CPB` 更像“新底座/未确认结构”的突破，而不是高热延续

当前 `CPB` 的条件层信号很明确：

1. `latest_confirmed_turn_type = NONE` 更好
2. `current_wave_age_band / current_wave_magnitude_band = UNSCALED` 更好
3. `streak_bucket = UP_4P` 更好
4. `EXTREME` age / magnitude 更差
5. `2B_TOP` 更差

这意味着第一版 `CPB` 更像“新底座、未确认、刚起动”的突破形态，  
而不是“已经过热后继续追强”。

### 3.4 `G6` 当前提供的是条件解释层，不是新的硬过滤器

当前 `G6` 已能正式回答：

`BOF / PB / CPB` 在什么历史尺环境下更值得出手？

但第一版结论仍应停留在：

1. 条件解释层
2. 优先级约束
3. Normandy 的附加判读

还不应直接升格为：

1. 硬过滤器
2. 新 alpha 来源
3. 主线默认参数改写

---

## 4. 当前边界

这份记录证明的是：

1. `G6` 已能把第四战场标签正式回灌到 `BOF / PB / CPB` 条件层
2. 第一版已能稳定输出 `baseline vs conditioning` 的相对改善/劣化
3. 当前第四战场已经不只会回答“这只票自身处于什么历史尺”，也开始能回答“哪些 pattern 在什么环境里更值得打”

这份记录暂时不声称：

1. 当前 `G6` 已经完成 Normandy 主 alpha 重写
2. `G6` 已足以直接决定 `MSS / IRS` 的最终去留
3. 当前条件层结论已经可以无代价写死成硬过滤器

---

## 5. 结论

`G6` 已完成。  
第四战场主线当前已从 `G0 / G1 / G2 / G3 / G4 / G5` 正式推进到 `G6` 结案，下一张卡应按顺序进入 `G7 / MSS-IRS refactor-or-retire decision`。
