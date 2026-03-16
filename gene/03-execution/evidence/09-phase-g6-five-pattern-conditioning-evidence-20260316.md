# G6 Evidence: 五形态条件层主库读数

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 运行对象

1. 主库：`G:\EmotionQuant_data\emotionquant.duckdb`
2. 计算日：`2026-02-24`
3. 读取函数：`compute_gene_conditioning(store, date(2026, 2, 24))`
4. 当前 schema：`v10`
5. 本轮写入：`108` 行

---

## 2. 五类 baseline

| pattern | sample_size | hit_rate | avg_forward_return_pct | median_forward_return_pct | avg_mae_pct | avg_mfe_pct |
|---|---:|---:|---:|---:|---:|---:|
| `bof` | 15107 | 0.582776 | 3.369605 | 2.167043 | 7.311051 | 12.961569 |
| `bpb` | 62 | 0.403226 | -1.569684 | -2.675845 | 13.170141 | 14.125807 |
| `cpb` | 16814 | 0.458071 | 0.933428 | -0.578283 | 5.256747 | 9.456609 |
| `pb` | 19713 | 0.443870 | 0.337060 | -1.020408 | 7.218192 | 9.811756 |
| `tst` | 23332 | 0.487999 | 0.800565 | -0.123502 | 5.800053 | 8.470176 |

---

## 3. 代表性改善条件

1. `bof / current_wave_direction = DOWN`
   - `sample_size = 14212`
   - `payoff_delta = +0.338385`
2. `bof / streak_bucket = UP_1`
   - `sample_size = 9587`
   - `payoff_delta = +1.311795`
3. `bpb / current_wave_direction = UP`
   - `sample_size = 54`
   - `payoff_delta = +0.518791`
4. `bpb / latest_two_b_confirm_type = 2B_TOP`
   - `sample_size = 22`
   - `payoff_delta = +1.117220`
5. `pb / current_wave_direction = DOWN`
   - `sample_size = 3460`
   - `payoff_delta = +0.552088`
6. `pb / current_wave_age_band = NORMAL`
   - `sample_size = 3795`
   - `payoff_delta = +0.631695`
7. `cpb / latest_confirmed_turn_type = NONE`
   - `sample_size = 8709`
   - `payoff_delta = +0.200818`
8. `cpb / current_wave_age_band = UNSCALED`
   - `sample_size = 8334`
   - `payoff_delta = +0.203999`
9. `tst / streak_bucket = UP_2_3`
   - `sample_size = 8474`
   - `payoff_delta = +0.392585`
10. `tst / current_wave_magnitude_band = STRONG / EXTREME`
    - `sample_size = 1057 / 803`
    - `payoff_delta = +1.622375 / +2.016668`

---

## 4. 代表性劣化条件

1. `bof / current_wave_direction = UP`
   - `sample_size = 895`
   - `payoff_delta = -5.373324`
2. `bof / streak_bucket = DOWN_1`
   - `sample_size = 1001`
   - `payoff_delta = -4.086828`
3. `bpb / latest_two_b_confirm_type = NONE`
   - `sample_size = 33`
   - `payoff_delta = -1.171994`
4. `pb / current_wave_direction = UP`
   - `sample_size = 16253`
   - `payoff_delta = -0.117531`
5. `cpb / current_wave_age_band = EXTREME`
   - `sample_size = 2227`
   - `payoff_delta = -0.989880`
6. `cpb / current_wave_magnitude_band = EXTREME`
   - `sample_size = 1469`
   - `payoff_delta = -1.488402`
7. `tst / streak_bucket = DOWN_2_3`
   - `sample_size = 579`
   - `payoff_delta = -1.028775`

---

## 5. 当前读数解释

1. `BOF` 仍是五类里最强的 baseline，但更像“下跌波里的第一脚修复”。
2. `BPB` 已接进第四战场，但当前样本只有 `62`，只能做 sparse watch readout。
3. `PB` 仍需要明确历史尺位置配合，不能只因看起来像回调就出手。
4. `TST` 已经形成大样本条件层，更像“已有波段里的支撑测试”。
5. `CPB` 仍偏 fresh-base / 无结构确认环境，对 `EXTREME / 2B_TOP` 更敏感。
6. 这些结果当前只服务 `Normandy` 条件层解释与优先级约束，不直接改写 `positioning` baseline。
