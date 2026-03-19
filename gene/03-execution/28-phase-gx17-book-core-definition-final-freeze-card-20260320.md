# GX17 / 书义根定义最终冻结卡
**状态**: `Proposal`
**日期**: `2026-03-20`
**类型**: `definition freeze`
**直接目标目录**: [`../01-full-design/`](../01-full-design/)

---

## 1. 目标

这张卡只回答一个问题：

`Gene 后续所有实现，究竟要以哪一套固定的趋势定义、趋势改变定义与市场寿命定义作为唯一根口径？`

---

## 2. 必须冻结的定义

1. 趋势层级：
   - `LONG`
   - `INTERMEDIATE`
   - `SHORT`
2. 中级波段角色：
   - `MAINSTREAM`
   - `COUNTERTREND`
3. 趋势改变事件：
   - `trendline break`
   - `1-2-3`
   - `2B`
4. 市场寿命框架四张 canonical 表：
   - `BULL_MAINSTREAM`
   - `BULL_COUNTERTREND`
   - `BEAR_MAINSTREAM`
   - `BEAR_COUNTERTREND`
5. 幅度轴口径：
   - `MAINSTREAM -> magnitude_pct`
   - `COUNTERTREND -> retracement_vs_prior_mainstream_pct`

---

## 3. 本卡必须交付

1. 书义定义冻结文档更新
2. 当前实现与书义差异矩阵
3. 术语表与字段映射表
4. 下游卡片统一引用口径

---

## 4. 关闭标准

1. `01-full-design` 中不再存在相互冲突的定义
2. `02-implementation-spec` 对每个定义都有唯一映射
3. 后续 GX18 ~ GX22 全部显式继承本卡口径

---

## 5. 一句话收口

`GX17` 要把书里的根定义彻底冻住，避免 Gene 后续继续“边做边改定义”。
