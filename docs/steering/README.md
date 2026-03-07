# Steering（治理铁律）

本目录存放 EmotionQuant 的核心治理文档，定义系统的不可变约束。

## 文档清单

### 1. `product.md` - 产品铁律
- 12 条系统铁律
- 6 模块职责边界
- 三套因子系统定位（MSS/IRS/PAS）
- v0.01 验证铁律

**适用对象**：所有开发者、所有模块

### 2. `a-stock-rules.md` - A股交易规则
- T+1 执行语义
- 涨跌停幅度（主板/创业板/科创板/北交所/ST）
- 手续费标准
- 基础过滤规则

**适用对象**：data/selector/broker 模块开发者

### 3. `architecture.md` - 技术架构快速参考
- 数据流概览
- L1-L4 分层
- 模块间契约
- CLI 入口

**定位**：快速参考卡片（1页纸），详细设计见 `docs/design-v2/`

### 4. `conventions.md` - 编码规范
- Python 版本要求
- OOP vs 纯函数分工
- 计算规范（禁止逐行循环）
- pydantic 用法
- 命名约定

**适用对象**：所有开发者

---

## 与其他文档的关系

| 本目录 | 详细设计 | 说明 |
|--------|---------|------|
| `product.md` | `docs/design-v2/system-baseline.md` | steering 定义"是什么"，design 定义"怎么做" |
| `architecture.md` | `docs/design-v2/architecture-master.md` | steering 是快速参考，design 是完整设计 |
| `a-stock-rules.md` | `docs/design-v2/broker-design.md` | steering 定义规则，design 定义实现 |
| `conventions.md` | `AGENTS.md` / `CLAUDE.md` | steering 定义规范，AGENTS 定义执行 |

---

## 使用指南

**新人入职**：
1. 先读 `product.md`（理解系统定位和铁律）
2. 再读 `a-stock-rules.md`（理解 A 股约束）
3. 最后读 `conventions.md`（理解编码规范）

**开发前**：
- 检查是否违反 `product.md` 的 12 条铁律
- 检查是否符合 `a-stock-rules.md` 的 A 股约束
- 检查是否符合 `conventions.md` 的编码规范

**设计评审**：
- `product.md` 是不可变约束（违反则拒绝）
- `architecture.md` 是参考框架（可优化但不可颠覆）
- `conventions.md` 是编码标准（可讨论但需统一）

---

**维护规则**：
- 本目录文档属于"治理冻结区"，变更需要充分理由
- 新增铁律必须有证据支持（消融实验、历史教训）
- 修改铁律必须评估影响面（是否破坏现有设计）
