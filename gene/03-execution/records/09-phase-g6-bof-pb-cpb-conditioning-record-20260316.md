# G6 记录: 五形态条件层统计已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 本次实现内容

1. `Store` schema 继续保持在 `v10`
2. `l3_gene_conditioning_eval` 继续作为第四战场条件层正式表
3. 本轮将 `compute_gene_conditioning(store, calc_date)` 从三形态扩成五形态，直接从 `l2_stock_adj_daily` 重构：
   - `BOF`
   - `BPB`
   - `PB`
   - `TST`
   - `CPB`
   五类 detector trigger 样本
4. 第一版 `G6` 仍不依赖主库当前并不完整的 `l3_signals / l4_orders / l4_trades`，而是显式改走“价格重构触发样本”口径
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
7. 第四战场现已补齐：
   - `gene/03-execution/evidence/`
   - `09-phase-g6-five-pattern-conditioning-evidence-20260316.md`

---

## 2. 主库真实读数

本次读取对象：

`G:\EmotionQuant_data\emotionquant.duckdb`

截至：

`2026-02-24`

主库 `G6` 结果：

1. `_meta_schema_version = 10`
2. `compute_gene_conditioning()` 本轮真实写入：`108` 行
3. 五类 baseline 样本量分别为：
   - `bof = 15107`
   - `bpb = 62`
   - `cpb = 16814`
   - `pb = 19713`
   - `tst = 23332`

五类 baseline 读数：

1. `bof`
   - `hit_rate = 0.582776`
   - `avg_forward_return_pct = 3.369605`
   - `median_forward_return_pct = 2.167043`
   - `avg_mae_pct = 7.311051`
   - `avg_mfe_pct = 12.961569`
2. `bpb`
   - `hit_rate = 0.403226`
   - `avg_forward_return_pct = -1.569684`
   - `median_forward_return_pct = -2.675845`
   - `avg_mae_pct = 13.170141`
   - `avg_mfe_pct = 14.125807`
3. `cpb`
   - `hit_rate = 0.458071`
   - `avg_forward_return_pct = 0.933428`
   - `median_forward_return_pct = -0.578283`
   - `avg_mae_pct = 5.256747`
   - `avg_mfe_pct = 9.456609`
4. `pb`
   - `hit_rate = 0.443870`
   - `avg_forward_return_pct = 0.337060`
   - `median_forward_return_pct = -1.020408`
   - `avg_mae_pct = 7.218192`
   - `avg_mfe_pct = 9.811756`
5. `tst`
   - `hit_rate = 0.487999`
   - `avg_forward_return_pct = 0.800565`
   - `median_forward_return_pct = -0.123502`
   - `avg_mae_pct = 5.800053`
   - `avg_mfe_pct = 8.470176`

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
3. `bpb / current_wave_direction = UP`
   - `sample_size = 54`
   - `hit_rate_delta = +0.022700`
   - `payoff_delta = +0.518791`
   - `mae_delta = -0.026362`
   - `mfe_delta = +0.138775`
4. `bpb / latest_two_b_confirm_type = 2B_TOP`
   - `sample_size = 22`
   - `hit_rate_delta = +0.142229`
   - `payoff_delta = +1.117220`
   - `mae_delta = -0.187947`
   - `mfe_delta = +0.469586`
5. `pb / current_wave_direction = DOWN`
   - `sample_size = 3460`
   - `hit_rate_delta = +0.027518`
   - `payoff_delta = +0.552088`
   - `mae_delta = -0.381368`
   - `mfe_delta = +0.767690`
6. `pb / current_wave_age_band = NORMAL`
   - `sample_size = 3795`
   - `hit_rate_delta = +0.027804`
   - `payoff_delta = +0.631695`
   - `mae_delta = -0.496224`
   - `mfe_delta = +0.224595`
7. `cpb / streak_bucket = UP_4P`
   - `sample_size = 4111`
   - `hit_rate_delta = +0.031348`
   - `payoff_delta = +0.627361`
   - `mae_delta = -0.540889`
   - `mfe_delta = +0.683119`
8. `cpb / latest_confirmed_turn_type = NONE`
   - `sample_size = 8709`
   - `payoff_delta = +0.200818`
9. `cpb / current_wave_age_band = UNSCALED`
   - `sample_size = 8334`
   - `payoff_delta = +0.203999`
10. `tst / streak_bucket = UP_2_3`
    - `sample_size = 8474`
    - `hit_rate_delta = +0.020379`
    - `payoff_delta = +0.392585`
    - `mae_delta = -0.773123`
    - `mfe_delta = +0.201158`
11. `tst / current_wave_magnitude_band = STRONG`
    - `sample_size = 1057`
    - `hit_rate_delta = +0.086267`
    - `payoff_delta = +1.622375`
    - `mae_delta = -1.461246`
    - `mfe_delta = +0.264452`
12. `tst / current_wave_magnitude_band = EXTREME`
    - `sample_size = 803`
    - `hit_rate_delta = +0.150855`
    - `payoff_delta = +2.016668`
    - `mae_delta = -1.635894`
    - `mfe_delta = +0.813138`

当前主库最有代表性的 `WORSE` 条件层：

1. `bof / current_wave_direction = UP`
   - `sample_size = 895`
   - `hit_rate_delta = -0.192832`
   - `payoff_delta = -5.373324`
2. `bof / streak_bucket = DOWN_1`
   - `sample_size = 1001`
   - `payoff_delta = -4.086828`
3. `bpb / latest_two_b_confirm_type = NONE`
   - `sample_size = 33`
   - `hit_rate_delta = -0.160802`
   - `payoff_delta = -1.171994`
4. `cpb / current_wave_age_band = EXTREME`
   - `sample_size = 2227`
   - `payoff_delta = -0.989880`
5. `cpb / current_wave_magnitude_band = EXTREME`
   - `sample_size = 1469`
   - `payoff_delta = -1.488402`
6. `cpb / latest_two_b_confirm_type = 2B_TOP`
   - `sample_size = 4585`
   - `payoff_delta = -0.488553`
7. `pb / current_wave_direction = UP`
   - `sample_size = 16253`
   - `payoff_delta = -0.117531`
8. `tst / streak_bucket = DOWN_2_3`
   - `sample_size = 579`
   - `hit_rate_delta = -0.030314`
   - `payoff_delta = -1.028775`
   - `mae_delta = +0.705179`
   - `mfe_delta = -1.353547`

---

## 3. 第一版 G6 结论

### 3.1 `BOF` 的 baseline 仍最强，但更像“下跌波里的第一脚反抽”

截至 `2026-02-24` 的主库样本里，`BOF` 仍是五类 pattern 里 baseline 最强的一类。  
但它最好的环境不是“已经在顺风主升里继续追”，而是：

1. `current_wave_direction = DOWN`
2. `streak_bucket = UP_1`

这说明当前 `BOF` 更像“下跌大波段中的第一脚向上修复/反抽”，而不是“顺主升继续追击”。  
相反，若当前已经处于 `UP` 背景，或者短期仍在 `DOWN_1 / FLAT`，读数会明显劣化。

### 3.2 `BPB` 已进入正式条件层，但当前还只是 sparse watch readout

`BPB` 这次已经被纳入 `G6` 的五形态条件层。  
但截至 `2026-02-24` 的主库样本量只有 `62`，明显比其他四类薄得多。

当前只能谨慎读取出两件事：

1. `current_wave_direction = UP` 略好
2. `latest_two_b_confirm_type = 2B_TOP` 略好

与此同时，`latest_two_b_confirm_type = NONE` 明显更差。  
这说明 `BPB` 当前可以被纳入解释层，但还远远不够支撑硬过滤或强 promotion。

### 3.3 `PB` 不是无脑回调就能打，只有落进明确历史尺后才略有改善

`PB` 的 baseline 在五类里仍偏弱。  
第一版主库结果里，`PB` 只在以下环境出现温和改善：

1. `current_wave_direction = DOWN`
2. `current_wave_age_band = NORMAL`
3. `current_wave_age_band = EXTREME`

这说明 `PB` 当前并不支持“只要像 pullback 就值得打”。  
它更像需要先知道这只票已经落在某个可识别的历史尺位置里，再去看 pullback 是否值得接。  
若处于 `UP` 背景，主库结果反而更差。

### 3.4 `TST` 已经形成大样本条件层，更像“强波段中的支撑测试”

`TST` 不是这次补进来后才有一点点样本，而是已经形成了 `23332` 的主库 baseline。  
当前最清楚的环境结论是：

1. `streak_bucket = UP_2_3` 更好
2. `current_wave_magnitude_band = STRONG / EXTREME` 更好
3. `streak_bucket = DOWN_2_3` 更差

这说明当前 `TST` 更像“已有波段惯性中的支撑测试/回踩确认”，  
而不是“逆着弱环境硬去抄底”。

### 3.5 `CPB` 更像“新底座/未确认结构”的突破，而不是高热延续

当前 `CPB` 的条件层信号很明确：

1. `latest_confirmed_turn_type = NONE` 更好
2. `current_wave_age_band / current_wave_magnitude_band = UNSCALED` 更好
3. `streak_bucket = UP_4P` 更好
4. `EXTREME` age / magnitude 更差
5. `2B_TOP` 更差

这意味着第一版 `CPB` 更像“新底座、未确认、刚起动”的突破形态，  
而不是“已经过热后继续追强”。

### 3.6 `G6` 当前提供的是条件解释层，不是新的硬过滤器

当前 `G6` 已能正式回答：

`BOF / BPB / PB / TST / CPB` 在什么历史尺环境下更值得出手？

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

1. `G6` 已能把第四战场标签正式回灌到 `BOF / BPB / PB / TST / CPB` 条件层
2. `BPB / TST` 已正式进入第四战场条件层，当前 `G6` 已完成五形态版
3. 第四战场现已补齐 `gene/03-execution/evidence/`，并为 `G6` 落下正式 evidence 文件
4. 第一版已能稳定输出 `baseline vs conditioning` 的相对改善/劣化
5. 当前第四战场已经不只会回答“这只票自身处于什么历史尺”，也开始能回答“哪些 pattern 在什么环境里更值得打”

这份记录暂时不声称：

1. 当前 `G6` 已经完成 Normandy 主 alpha 重写
2. `G6` 已足以直接决定 `MSS / IRS` 的最终去留
3. 当前条件层结论已经可以无代价写死成硬过滤器

---

## 5. 结论

`G6` 已完成。  
第四战场主线当前已从 `G0 / G1 / G2 / G3 / G4 / G5` 正式推进到 `G6` 结案，下一张卡应按顺序进入 `G7 / MSS-IRS refactor-or-retire decision`。
