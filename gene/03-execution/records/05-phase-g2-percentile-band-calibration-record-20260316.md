# G2 记录: 历史寿命分布与 65/95 校准已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 本次实现内容

1. 将 `Store` schema 正式升级到 `v6`
2. 新增 `l3_gene_distribution_eval` 研究表
3. 将 `P65 / P95` 分布阈值与 band 标签正式回写到：
   - `l3_stock_gene`
   - `l3_gene_wave`
4. 将 `wave_age_band` 固定为第四战场正式字段
5. 将 `compute_gene()` 扩展为在窗口结束日输出当前波段的自历史分布带与基础赔率读数

---

## 2. 主库真实读数

本次读取对象：

`G:\EmotionQuant_data\emotionquant.duckdb`

截至：

`2026-02-24`

主库 `G2` 结果：

1. `_meta_schema_version = 6`
2. `compute_gene()` 本轮真实重算写入：`1,854,141` 行
3. `l3_gene_distribution_eval`: `10,948` 行
   - `5,474` 只股票
   - 每只股票 `2` 条正式读数：`magnitude_pct` 与 `duration_trade_days`

`2026-02-24` 当日当前波段 band 分布：

1. `magnitude band`
   - `NORMAL`: `4,574`
   - `STRONG`: `731`
   - `EXTREME`: `158`
   - `UNSCALED`: `11`
2. `wave_age_band`
   - `STRONG`: `3,154`
   - `NORMAL`: `1,939`
   - `EXTREME`: `370`
   - `UNSCALED`: `11`

当日全市场自历史阈值中位数：

1. `magnitude_pct`
   - `median P65 = 10.25%`
   - `median P95 = 21.50%`
2. `duration_trade_days`
   - `median P65 = 5.0`
   - `median P95 = 9.6`

---

## 3. 第一版 G2 结论

### 3.1 `magnitude` 的分布带已经能拉开差异

按 `2026-02-24` 主库读数看：

1. `NORMAL` 的平均 continuation rate = `17.16%`
2. `STRONG` 的平均 continuation rate = `14.49%`
3. `EXTREME` 的平均 continuation rate = `14.70%`
4. `NORMAL` 的平均 median forward return = `-4.35%`
5. `EXTREME` 的平均 median forward return = `-7.47%`

这说明 `magnitude` 进入强波段、极端波段之后，后续推进的顺畅度继续下降，衰竭读数更重。

### 3.2 `duration` 的分布带已可落库，但解释力仍偏弱

按 `2026-02-24` 主库读数看：

1. `NORMAL` 的平均 continuation rate = `15.15%`
2. `STRONG` 的平均 continuation rate = `16.12%`
3. `EXTREME` 的平均 continuation rate = `17.02%`
4. 三段之间存在差异，但顺序不如 `magnitude` 清晰

也就是说，`duration` 现在已经可以作为正式“年龄位置标签”使用，但还不足以替代 `magnitude` 成为当前核心硬尺。

### 3.3 `65 / 95` 已被固定为“位置标签”，而不是交易参数

`G2` 当前正式回答的是：

`当前波段在它自己的历史里位于哪里`

而不是：

`只要进了某个 band 就直接下单`

---

## 4. 当前边界

这份记录证明的是：

1. `G2` 已能在主库稳定落表
2. `P65 / P95` 三层分带已具备正式字段与主库真实读数
3. `wave_age_band` 已能作为后续 `G4 / G6` 的统一口径
4. `magnitude` 的历史分布带当前比 `duration` 更有解释力

这份记录暂时不声称：

1. `G4` 的“个股自历史标尺”已经完成最终验证
2. `G3` 的 `1-2-3 / 2B` 正式结构标签已经稳定
3. `G6` 的 `BOF / PB / CPB` 条件层已经被第四战场成功回灌

---

## 5. 结论

`G2` 已完成。  
第四战场当前主线已从 `G0 / G1` 正式推进到 `G2` 结案，下一张卡应按顺序进入 `G3 / structure label calibration`。
