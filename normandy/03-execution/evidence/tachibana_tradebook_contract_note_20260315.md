# Tachibana Tradebook Contract Note

**文档版本**：`v0.01`  
**文档状态**：`Active`  
**日期**：`2026-03-15`  
**适用范围**：`Normandy / Track T0 / tradebook extraction contract`

---

## 1. 目标

本 note 只做三件事：

1. 固定 `1975.01-1976.12 Pioneer 交易谱` 的第一轮抽取边界
2. 明确哪些字段已经是机器真值，哪些字段仍然需要人工确认
3. 固定首版结构化台账的最小字段和置信度口径

---

## 2. 当前源材料

第一轮以以下材料为主：

1. `G:\《股市浮沉二十载》\2012.(Japan)【立花义正】\丽花义正-交易谱（1975.01-1976.12）\你也能成为股票操作高手立花义正-Pioneer交易记录19751976.xlsx`
2. `G:\《股市浮沉二十载》\2012.(Japan)【立花义正】\丽花义正-交易谱（1975.01-1976.12）\7501.pdf` 到 `7612.pdf`
3. `G:\《股市浮沉二十载》\2012.(Japan)【立花义正】\你也能成为股票操作高手（立花义正）PDF转图片版`

当前优先级固定为：

1. `xlsx calendar/close` 作为日历与收盘价骨架真值
2. `pdf / 图片版` 作为交易标记人工复核来源
3. 任何去年的总结稿都不充当事实源

---

## 3. 当前已确认的机器可读边界

对 `xlsx` 的实际检查结果如下：

1. 第一张表包含 `日期 / 假日 / 收盘价 / 成交价 / 交易 / 未平仓` 的表头结构
2. `日期` 与 `收盘价` 可以稳定作为单元格值读取
3. `交易 / 未平仓` 的标记在工作簿中并未以可稳定读取的单元格值存在
4. 工作簿的 drawing 仅发现 chart 对象，没有发现能直接恢复交易标记的图片层

因此当前固定判断为：

`xlsx 不是最终交易真相表，而是日历与价格骨架。`

---

## 4. 第一轮数据分层

### 4.1 `A_price`

定义：

1. 来自 `xlsx` 可直接读取的日期和收盘价
2. 可直接进入首版 ledger scaffold

当前字段：

1. `date`
2. `holiday_tag`
3. `close`
4. `source_sheet`
5. `source_row`

### 4.2 `B_calendar`

定义：

1. 来自 `xlsx` 的日历骨架
2. 无收盘价的非交易日、周末、假日也保留

当前字段：

1. `date`
2. `holiday_tag`
3. `is_trading_day`

### 4.3 `C_trade_manual`

定义：

1. 来自 `pdf / 图片版 / 人工标注` 的交易动作与未平仓信息
2. 在未人工复核前，不能写成正式真值

当前待补字段：

1. `execution_price`
2. `action`
3. `buy_units`
4. `sell_units`
5. `open_units`
6. `position_state`
7. `reason_tag`
8. `state_tag`

---

## 5. 首版 ledger scaffold 契约

首版结构化台账当前固定为：

1. 一行对应一个自然日
2. 先保留全部日历，不只保留交易日
3. 已确认字段直接写入
4. 交易字段留空，等待人工抽取补录

当前文件：

1. `normandy/03-execution/evidence/tachibana_tradebook_ledger_scaffold_1975_1976.csv`
2. `normandy/03-execution/evidence/tachibana_tradebook_scaffold_digest_20260315.json`

当前关键列：

1. `date`
2. `month`
3. `symbol`
4. `calendar_index`
5. `holiday_tag`
6. `is_trading_day`
7. `close`
8. `execution_price`
9. `action`
10. `buy_units`
11. `sell_units`
12. `open_units`
13. `position_state`
14. `reason_tag`
15. `state_tag`
16. `source`
17. `source_sheet`
18. `source_row`
19. `trade_marker_readable`
20. `confidence`
21. `note`

---

## 6. 当前统计结论

首版机器抽取当前固定下列统计：

1. `24` 个自然月
2. `731` 个日期行
3. `569` 个含收盘价的交易日
4. `162` 个带假日标签的日期行
5. `0` 个可直接从 `xlsx` 单元格值恢复的交易标记行

这意味着：

`Track T0` 当前不是“自动读出完整交易谱”，而是“先固定价格日历真值，再逐步回填交易动作真值”。`

---

## 7. 当前 no-go

第一轮明确禁止：

1. 把空白交易列自动脑补成买卖记录
2. 把 OCR 误读直接升格为正式账本真值
3. 在未标明置信度时，把手工整理和机器真值混写

---

## 8. 下一步

下一个实际动作应是：

1. 以月为单位，结合 `7501.pdf` 到 `7612.pdf` 与图片版，逐月回填 `C_trade_manual`
2. 首先完成 `1975-01` 的人工抽取样板
3. 形成 `manual_action / manual_open_units / manual_note` 的第一批真值样本
