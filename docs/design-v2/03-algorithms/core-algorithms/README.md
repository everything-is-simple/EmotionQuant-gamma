# 核心算法设计（v0.01-v0.06）

**版本**: v0.01 正式版  
**创建日期**: 2026-03-07  
**状态**: Active（算法级 SoT）  
**上游文档**: `system-baseline.md`  
**理论来源**: `docs/Strategy/`

---

## 1. 目录定位

本目录存放 EmotionQuant 核心算法设计文档，覆盖 **三大核心模块**：

1. **MSS**（Market Sentiment System）：市场情绪系统
2. **IRS**（Industry Rotation System）：行业轮动系统
3. **PAS**（Price Action Signals）：价格行为信号

**与旧版设计的区别**：
- 旧版（`docs/reference/core-algorithms/`）：包含 MSS/IRS/PAS/Validation/Integration 五模块，是研究材料
- 新版（本目录）：聚焦 MSS/IRS/PAS 三模块，是 v0.01-v0.06 的执行口径

---

## 2. 文件结构

```
docs/design-v2/core-algorithms/
├── README.md                        # 本文件
├── mss-algorithm.md                 # MSS 算法设计（市场情绪）
├── irs-algorithm.md                 # IRS 算法设计（行业轮动）
├── pas-algorithm.md                 # PAS 算法设计（价格行为）
└── down-to-top-integration.md       # v0.01-plus 集成模式（软评分）
```

**设计原则**：
- 每个模块一个文件
- 算法定义 + 理论来源 + 版本演进
- 不再拆分为 algorithm/data-models/api/information-flow 四文件（过度设计）

---

## 3. 模块职责与理论来源

### 3.1 MSS：市场情绪系统

**职责**：计算市场整体情绪温度、判定情绪状态（BULLISH/NEUTRAL/BEARISH）  
**输入**：`l2_market_snapshot`（市场截面数据）  
**输出**：`l3_mss_daily`（date, score, signal）  
**理论来源**：
- 《2024.大盘情绪交易系统》（三维观测、七阶段周期、对称设计）
- 《市场情绪表-手工》5年实践（2020-2025）

**核心算法**：
- 六因子框架（market_coefficient, profit_effect, loss_effect, continuity, extreme, volatility）
- 权重：17% + 34% + 34% + 5% + 5% + 5%
- 三态阈值：65/35（v0.01），软评分（v0.02+）

**版本演进**：
- v0.01: 三态硬门控 + 固定阈值
- v0.02: 软评分模式 + 阈值敏感性测试
- v0.03: 七阶段周期识别
- v0.04: 趋势方向识别
- v0.05: 动态仓位建议
- v0.06: 自适应阈值

### 3.2 IRS：行业轮动系统

**职责**：评估行业相对强度、输出行业排名（1-31）  
**输入**：`l2_industry_daily`（行业日线）+ `l1_index_daily`（基准指数）  
**输出**：`l3_irs_daily`（date, industry, score, rank）  
**理论来源**：
- 申万行业分类标准（SW2021 一级 31 行业）
- 行业轮动四驱动力（经济周期、资金、政策、技术）

**核心算法**：
- 两因子框架（RS 相对强度 55%, CF 资金流向 45%）
- 排名规则：唯一、稳定、可复现
- Top-N 过滤（v0.01），软评分（v0.02+）

**版本演进**：
- v0.01: 两因子 + Top-N 硬过滤
- v0.02: 软评分模式 + 龙头强度
- v0.03: 牛股基因聚合
- v0.04: 行业生命周期
- v0.05: 政策事件驱动
- v0.06: 自适应权重

### 3.3 PAS：价格行为信号

**职责**：检测价格行为形态、生成买入信号  
**输入**：候选池 + `l2_stock_adj_daily`（个股日线）  
**输出**：`l3_signals`（signal_id, code, signal_date, action, pattern, bof_strength）  
**理论来源**：
- Lance Beggs《YTC Price Action Trader》（五形态：BPB/PB/TST/BOF/CPB）
- 许佳冲《裸K线交易法》（BOF 详解、Pin Bar）
- Bob Volman《外汇超短线交易》（七种结构、临界点技术）
- Al Brooks《Price Action》（失败处理）
- 立花义正（极端情绪交易）

**核心算法**：
- detector 模式（一形态一检测器）
- BOF 四条件（假突破 + 收回 + 位置 + 量能）
- 单形态回测验证

**版本演进**：
- v0.01: BOF 单形态闭环
- v0.02: BPB 形态接入
- v0.03: TST/PB 形态接入
- v0.04: CPB 形态接入 + 失败处理
- v0.05: 形态强度评分
- v0.06: 自适应参数

---

## 4. 集成模式

### 4.1 v0.01：Top-Down 硬门控

```
MSS gate（BEARISH → 不出手）
  ↓
IRS filter（只看 Top-N 行业）
  ↓
PAS detect（BOF 触发）
  ↓
Broker（风控 + 撮合）
```

**问题**：
- MSS 硬门控误杀机会
- IRS 硬过滤压缩样本
- 信息量损失严重

### 4.2 v0.02+：Down-to-Top 软评分

```
基础过滤（流动性/ST/停牌）
  ↓
PAS detect（BOF 触发）
  ↓
叠加 IRS/MSS 评分
  ↓
综合排序 Top-N
  ↓
Broker（风控 + 撮合）
```

**改进**：
- MSS/IRS 作为后置评分项
- 保留所有 BOF 信号，只排序
- 信息量最大化利用

详见：`down-to-top-integration.md`

---

## 5. 使用指南

### 5.1 如何阅读这些文档

**首次阅读顺序**：
1. `mss-algorithm.md` → 理解市场情绪系统
2. `irs-algorithm.md` → 理解行业轮动系统
3. `pas-algorithm.md` → 理解价格行为信号
4. `down-to-top-integration.md` → 理解集成模式演进

**实现时阅读顺序**：
1. 先读 `system-baseline.md` 确认执行语义
2. 再读对应模块的 `*-algorithm.md` 确认算法定义
3. 参考 `docs/Strategy/` 理解理论来源
4. 查看 `docs/spec/v0.01/evidence/` 验证消融证据

### 5.2 核心算法链路流程

```text
Data Layer (L1/L2)
  ↓
┌─────────────────────────────┐
│  MSS  │  IRS  │  (并行计算)
└─────────────────────────────┘
  ↓
Selector (基础过滤 + 候选池)
  ↓
PAS (形态检测 + 信号生成)
  ↓
  v0.01: Top-Down 硬门控
  v0.02+: Down-to-Top 软评分
  ↓
Broker (风控 + 撮合)
  ↓
Report (回测报告 + 复盘)
```

### 5.3 关键设计原则

1. **情绪优先**：MSS 是主信号来源，其他系统必须与情绪周期对齐
2. **形态优先**：PAS 形态触发是核心，MSS/IRS 是辅助评分
3. **模块独立**：每个模块可独立单测，不依赖其他模块启动
4. **结果契约**：模块间只传 pydantic 对象，不传内部中间特征
5. **版本演进**：v0.01-v0.06 分六个阶段，每阶段独立验收

---

## 6. 边界说明

### 6.1 冻结区

本目录属于核心算法冻结区，以下内容**只能实现，不得改写语义**：
- 算法定义、评分口径、门禁逻辑
- 数据模型、字段定义、枚举口径
- 接口契约、输入输出、异常语义

### 6.2 允许变更范围

仅在以下场景允许修改：
1. 修复设计缺陷（必须有证据编号）
2. 补充缺失字段/枚举（必须有实现需求证据）
3. 优化算法性能（不改语义，仅优化计算效率）
4. 版本升级（v0.01 → v0.02，必须通过验收）

### 6.3 禁止事项

1. 以单技术指标替代情绪因子
2. 修改核心算法链路依赖关系
3. 绕过消融验证直接上线新因子
4. 跨版本混用算法（如 v0.01 用 v0.03 的周期识别）

---

## 7. 版本演进总览

| 版本 | MSS | IRS | PAS | 集成模式 | 验收标准 |
|------|-----|-----|-----|---------|---------|
| v0.01 | 三态硬门控 | Top-N 硬过滤 | BOF 单形态 | Top-Down | EV>=0, PF>=1.05, MDD<=25%, trade>=60 |
| v0.02 | 软评分模式 | 软评分 + 龙头 | BOF + BPB | Down-to-Top | EV 改善>=10%, MDD 改善>=20% |
| v0.03 | 七阶段周期 | 牛股基因 | TST + PB | 软评分 | 周期识别>=70%, 组合回测通过 |
| v0.04 | 趋势方向 | 行业生命周期 | CPB + 失败处理 | 软评分 | 趋势识别>=65%, 失败处理减亏>=20% |
| v0.05 | 动态仓位 | 政策事件 | 形态强度评分 | 软评分 | MDD 改善>=20%, Gene 覆盖历史 |
| v0.06 | 自适应阈值 | 自适应权重 | 自适应参数 | 软评分 | EV 改善>=15%, 可解释性 |

**晋级门槛**：
- 当前版本连续两个评估窗通过验收
- 新增模块单独回测通过
- 不破坏执行语义和结果契约

---

## 8. 与旧版设计的关系

### 8.1 旧版设计（`docs/reference/core-algorithms/`）

**内容**：
- MSS/IRS/PAS/Validation/Integration 五模块
- 每模块四文件（algorithm/data-models/api/information-flow）
- 完整的因子验证和权重桥接设计

**定位**：
- 研究材料和历史参考
- 不作为 v0.01 执行口径
- 保留用于未来版本参考

### 8.2 新版设计（本目录）

**内容**：
- MSS/IRS/PAS 三模块
- 每模块一文件（algorithm + 理论来源 + 版本演进）
- 聚焦 v0.01-v0.06 执行路径

**定位**：
- 当前执行口径
- 算法级 SoT
- 与 `system-baseline.md` 配合使用

### 8.3 迁移策略

**v0.01-v0.02**：
- 不引入 Validation/Integration 模块
- MSS/IRS/PAS 直接集成
- 消融验证替代因子验证

**v0.03+**：
- 根据实际需要决定是否引入 Validation
- 如果引入，参考旧版设计但简化实现
- 不追求"完美设计"，追求"可用系统"

---

## 9. 参考资料

### 9.1 理论来源

- `docs/Strategy/MSS/` - MSS 理论基础
- `docs/Strategy/IRS/` - IRS 理论基础
- `docs/Strategy/PAS/` - PAS 理论基础

### 9.2 系统设计

- `docs/design-v2/system-baseline.md` - 系统基线（执行语义）
- `docs/design-v2/selector-design.md` - Selector 模块设计
- `docs/design-v2/strategy-design.md` - Strategy 模块设计
- `docs/design-v2/broker-design.md` - Broker 模块设计

### 9.3 证据与验收

- `docs/spec/v0.01/evidence/` - 消融实验证据
- `docs/spec/v0.01/roadmap/` - 版本路线图
- `docs/design-v2/sandbox-review-standard.md` - 沙盘评审标准

### 9.4 历史参考

- `docs/reference/core-algorithms/` - 旧版算法设计（研究材料）
- `docs/reference/未来之路/` - 系统观察框架（非约束）

---

## 10. 维护规则

### 10.1 更新原则

1. **版本同步**：算法文档版本号与系统版本号同步
2. **证据驱动**：算法变更必须有消融实验证据支持
3. **向后兼容**：新版本不破坏旧版本的执行语义
4. **文档先行**：算法变更先更新文档，再修改代码

### 10.2 质量标准

1. **准确性**：算法定义清晰、无歧义
2. **完整性**：覆盖理论来源、算法定义、版本演进
3. **可追溯**：每个设计决策都有理论依据或证据支持
4. **可执行**：开发者可直接根据文档实现算法

### 10.3 冲突处理

若本目录文档与其他文档冲突：
1. 执行语义以 `system-baseline.md` 为准
2. 算法定义以本目录文档为准
3. 理论来源以 `docs/Strategy/` 为准
4. 证据验证以 `docs/spec/v0.01/evidence/` 为准

---

**文档状态**：Active  
**下一步行动**：
1. 完成 v0.01 BOF 单形态回测验证
2. 准备 v0.02 BPB 形态接入
3. 验证 Down-to-Top 软评分模式
4. 补充 Al Brooks 和 Bob Volman 理论梳理
