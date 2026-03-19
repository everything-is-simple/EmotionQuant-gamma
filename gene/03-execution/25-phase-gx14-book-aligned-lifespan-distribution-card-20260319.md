# GX14 / 书义寿命分布图重定卡
**状态**: `Active`  
**日期**: `2026-03-19`  
**类型**: `book-aligned semantic correction`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`能否把 Gene 的寿命统计，从“p65 / p95 尾部年龄刀”改回《专业投机原理》里那张以中级主要走势为对象、以波动幅度 + 持续时间构成连续分布、再按四分位读取阶段的寿命分布图。`

---

## 2. 为什么必须开这张卡

`2026-03-19` 的书页复核已经把目标重新钉死：

1. 长期趋势 = `牛市 / 熊市`
2. 真正要统计的是：
   `长期趋势里，夹在两个次级折返走势之间的中级主要走势`
3. 寿命图不该继续把眼光钉在 `p65 ~ p95` 的老年尾部
4. 应回到：
   `first / second / third / fourth quarter`
5. 分布图必须同时保留：
   - `波段时间`
   - `波动幅度`
   - `连续分布`

这意味着 `GX10` 只补“参考基础”还不够，必须再开一张更窄的卡，把书里的寿命图本身做对。

---

## 3. 本卡必须交付的最小语义

### 3.1 样本对象收口

寿命参考样本必须优先收口到：

`INTERMEDIATE + MAINSTREAM + long-context-consistent`

不允许继续把次级折返和主要走势混成一锅。

### 3.2 四分位分布读数

寿命读数必须支持：

1. `FIRST_QUARTER`
2. `SECOND_QUARTER`
3. `THIRD_QUARTER`
4. `FOURTH_QUARTER`

不允许继续只留下 `NORMAL / STRONG / EXTREME` 这种偏尾部的压缩语义。

### 3.3 时间 + 幅度连续分布

至少要正式输出：

1. `duration quartile thresholds`
2. `magnitude quartile thresholds`
3. `lifespan_joint_percentile`
4. `lifespan_joint_band`

---

## 4. 本卡允许修改

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. `Phase 9 / duration` 相关 card

---

## 5. 本卡明确不做

1. 不直接宣布新的 runtime hard gate
2. 不直接打开 `17.9`
3. 不直接替代 `GX13` 的统计重跑

---

## 6. 当前阶段结果

本卡当前已经落下第一版代码修正：

1. `band` 读数已改成 quartile semantics
2. `duration / magnitude` 已新增 `q25 / q50 / q75` 阈值字段
3. `lifespan` 参考样本已优先锁回 `INTERMEDIATE + MAINSTREAM`
4. `tests/unit/selector/test_gene.py` 已通过定向验证

但本卡尚未完成，因为：

1. `GX13` 还没在这条新 surface 上重跑
2. `17.8` 还没基于这条新寿命图落正式 evidence

---

## 7. 下一步

本卡完成前，`17.8` 的 truthful 角色应读成：

`book-aligned lifespan distribution rerun first`

一句话状态：

`GX14` 负责把寿命统计图本体纠正到书义位置，再让下游重跑去验证它值不值得进 runtime。`
