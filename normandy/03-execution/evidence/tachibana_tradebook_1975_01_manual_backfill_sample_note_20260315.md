# Tachibana Tradebook 1975-01 Manual Backfill Sample Note

**文档版本**：`v0.01`  
**文档状态**：`Active`  
**日期**：`2026-03-15`  
**适用范围**：`Normandy / Track T0 / 1975-01 manual backfill sample`

---

## 1. 本 note 的定位

本 note 不是报告“1975-01 已完成人工回填”，而是固定 `1975-01` 首个月样板的事实边界。

当前已经完成的是：

1. 从 `ledger scaffold` 中切出 `1975-01` 月度样板
2. 对 `7501.pdf` 和 `丽花义正-交易谱.pdf` 第 1 页进行视觉核对
3. 确认当前月页仅提供日期、假日、收盘价骨架，不提供交易标记真值

---

## 2. 当前已确认事实

`1975-01` 当前可稳定确认的事实只有下面这些：

1. 自然月范围：`1975-01-01` 到 `1975-01-31`
2. 日历骨架完整
3. 假日与周日标签可读
4. 收盘价可读

当前不能确认的事实：

1. 哪一天发生 `买`
2. 哪一天发生 `卖`
3. 每次交易的 `成交价`
4. 每天的 `未平仓`
5. `probe / mother / ladder` 的真实路径

---

## 3. 为什么现在不能做正式回填

对 `7501.pdf` 的实际视觉检查显示：

1. 页内存在完整表头：`日期 / 假日 / 收盘价 / 成交价 / 交易 / 未平仓`
2. 但 `成交价 / 买 / 卖 / 多 / 空` 区域为空白
3. `xlsx` 的对应列也同样为空白

因此当前结论固定为：

`1975-01 月页是日历价格模板，不是交易动作原件。`

这意味着：

1. 现在可以制作 `待确认样板`
2. 但不能制作 `正式真值账本`

---

## 4. 当前样板文件

本轮生成的 `1975-01` 样板文件为：

1. `tachibana_tradebook_1975_01_manual_backfill_sample.csv`

该文件的作用不是声明交易事实，而是：

1. 固定 `1975-01` 的日期与价格骨架
2. 为后续手工回填预留标准字段
3. 把 `unresolved` 状态显式写出，避免后续把模板误当真值

---

## 5. 当前字段口径

样板文件新增的手工字段包括：

1. `manual_action`
2. `manual_execution_price`
3. `manual_buy_units`
4. `manual_sell_units`
5. `manual_open_units`
6. `manual_state_tag`
7. `manual_status`
8. `manual_note`

当前统一默认：

1. `manual_status = unresolved_source_missing_trade_markers`
2. `manual_note = January source page is blank in trade-marker area; factual trade backfill is blocked.`

---

## 6. 当前真正的 blocker

`1975-01` 当前缺的不是抽取脚本，而是事实源。

只要没有下面任一类材料，就不能把 1 月做成正式真值月：

1. 带真实交易标记的原始交易谱页
2. 你手工录入过买卖和未平仓的版本
3. 能证明交易动作的额外对照材料

---

## 7. 当前一句话结论

`1975-01` 的首个月样板已经建立，但由于月页本身不含交易标记，当前只能作为待确认模板，不能被升格为正式人工回填真值。`
