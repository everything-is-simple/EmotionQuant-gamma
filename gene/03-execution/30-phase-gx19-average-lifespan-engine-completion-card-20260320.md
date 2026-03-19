# GX19 / 平均寿命框架引擎补完卡
**状态**: `Active`
**日期**: `2026-03-20`
**类型**: `engine completion`
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`市场平均寿命框架，能不能从“已有部分字段”补成一套完整、诚实、可复用的统计引擎？`

---

## 2. 当前缺口

1. `history_sample_size = 0` 时仍有伪中性概率
2. `COUNTERTREND` 侧的平均寿命框架还不完整
3. 市场级与个股级的 remaining / aged / odds 语义还未完全统一
4. `UNSCALED` 的空值合同尚未收死

---

## 3. 本卡必须交付

1. `UNSCALED -> NULL odds` 正式实现
2. `MAINSTREAM / COUNTERTREND` 双侧平均寿命引擎
3. 市场与个股共享的寿命概率合同
4. 对应单测与边界样本测试

---

## 4. 关闭标准

1. 不再出现“无历史样本 = 0.5 / 1.0 假中性”
2. 四张 surface 都能 truthfully 产出 remaining / aged / odds
3. 书义字段和数据库字段一一对应

---

## 5. 一句话收口

`GX19` 要把平均寿命框架从“半套字段”补成完整引擎，确保统计结论诚实可用。
