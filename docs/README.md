# EmotionQuant 文档导航

**版本**: v2.0  
**最后更新**: 2026-03-07  
**文档状态**: Active

---

## 📖 文档定位

`docs/` 目录是 EmotionQuant 系统的**知识中枢**，按照"三大支柱 + 三大支撑"组织：

### 三大支柱（核心）

1. **design-v2/** - 系统设计（What to build）
2. **observatory/** - 系统观察与验证（How to verify）
3. **Strategy/** - 理论基础（Why we build this way）

### 三大支撑（辅助）

4. **steering/** - 治理铁律（不可变约束）
5. **spec/** - 分阶段归档（版本演进）
6. **workflow/** - 工作流程（执行规范）

### 其他

7. **reference/** - 参考资料（外部材料）

---

## 📁 目录结构总览

```
docs/
│
├── 三大支柱（核心）/
│   ├── design-v2/              # 系统设计（What to build）
│   │   ├── system-baseline.md  # 单一事实源 ⭐
│   │   ├── core-algorithms/    # 算法级 SoT（MSS/IRS/PAS）
│   │   └── *-design.md         # 模块级设计
│   │
│   ├── observatory/            # 系统观察与验证（How to verify）
│   │   ├── god-view-8-perspectives-v0.01.md    # 宏观观察
│   │   └── sandbox-review-standard.md          # 微观验证
│   │
│   └── Strategy/               # 理论基础（Why we build this way）
│       ├── MSS/                # 市场情绪系统理论
│       ├── IRS/                # 行业轮动系统理论
│       └── PAS/                # 价格行为信号理论
│
├── 三大支撑（辅助）/
│   ├── steering/               # 治理铁律（不可变约束）
│   │   ├── product.md          # 12条系统铁律
│   │   ├── a-stock-rules.md    # A股交易规则
│   │   ├── architecture.md     # 技术架构快速参考
│   │   └── conventions.md      # 编码规范
│   │
│   ├── spec/                   # 分阶段归档（v0.01-v0.06）
│   │   ├── common/             # 跨版本治理记录
│   │   └── v0.01-v0.06/        # 各版本路线图、证据、记录
│   │
│   └── workflow/               # 工作流程（执行规范）
│       └── 6A-WORKFLOW.md      # 标准工作流
│
└── reference/                  # 参考资料（外部材料）
    ├── A股市场交易规则-tushare版.md
    ├── A股涨跌停板制度-tushare版.md
    ├── A股申万行业指数-tushare版.md
    └── temp-files-guide.md
```

---

## 🎯 三大支柱详解

### 1. design-v2/ - 系统设计（What to build）

**定位**：回答"系统设计成什么样"

**核心文档**：
- `system-baseline.md` - 系统基线（单一事实源）⭐
- `architecture-master.md` - 架构总览
- `core-algorithms/` - 算法级 SoT
  - `mss-algorithm.md` - MSS 算法设计
  - `irs-algorithm.md` - IRS 算法设计
  - `pas-algorithm.md` - PAS 算法设计
  - `down-to-top-integration.md` - 集成模式演进
- 模块级设计：
  - `data-layer-design.md` - Data 模块
  - `selector-design.md` - Selector 模块
  - `strategy-design.md` - Strategy 模块
  - `broker-design.md` - Broker 模块
  - `backtest-report-design.md` - Backtest & Report 模块

**使用场景**：
- 新功能开发前查阅设计规范
- 模块边界不清时查阅职责定义
- 算法实现时查阅算法设计

**权威性**：
- `system-baseline.md` 是唯一权威入口
- 若其他文档与 baseline 冲突，以 baseline 为准

---

### 2. observatory/ - 系统观察与验证（How to verify）

**定位**：回答"如何验证系统质量"

**核心文档**：
- `god-view-8-perspectives-v0.01.md` - 宏观观察（八维视角）
  - 市场/行业/个股/形态/风控/数据/执行/生态
  - v0.01-v0.06 版本演进建议
  - 分桶/分层/生态管理思路
  
- `sandbox-review-standard.md` - 微观验证（七维评审）
  - Schema契合/调用链完整性/幂等与确定性
  - 状态机完整性/时序语义/边界冲突/报告口径
  - 偏差清单（A-S，44项）
  - 定稿门禁与连环失效检测

**使用场景**：
- 版本规划时使用 god-view 进行全局审视
- 关键模块开发完成后使用 sandbox-review 进行沙盘推演
- 版本发布前使用 sandbox-review 进行全链路验证

**配套关系**：
- god-view = 宏观观察（战略层面）
- sandbox-review = 微观验证（战术层面）

---

### 3. Strategy/ - 理论基础（Why we build this way）

**定位**：回答"为什么这样设计"

**核心文档**：
- `README.md` - 理论基础资料梳理总览
- `theoretical-foundations.md` - 理论基础与方法论溯源

**理论来源**：
- **MSS/** - 市场情绪系统理论（2份）
  - `market-sentiment-system-2024-analysis.md` - 《大盘情绪交易系统》理论梳理
  - `manual-sentiment-tracking-experience.md` - 《市场情绪表-手工》实践经验
  
- **IRS/** - 行业轮动系统理论（1份）
  - `shenwan-industry-classification.md` - 申万行业分类标准
  
- **PAS/** - 价格行为信号理论（4份）
  - `lance-beggs-ytc-analysis.md` - Lance Beggs YTC 系列
  - `xu-jiachong-naked-kline-analysis.md` - 许佳冲《裸K线交易法》
  - `volman-ytc-mapping.md` - Bob Volman 与 YTC 映射 ⭐
  - `tachibana-yoshimasa-analysis.md` - 立花义正方法论

**使用场景**：
- 理解算法设计的理论依据
- 学习价格行为交易的原理
- 对比不同作者的方法论

**完成度**：7/9（78%），待完成2份不影响 v0.01-v0.03 实现

---

## 🛠️ 三大支撑详解

### 4. steering/ - 治理铁律（不可变约束）

**定位**：定义系统的不可变约束

**核心文档**：
- `product.md` - 12条系统铁律
- `a-stock-rules.md` - A股交易规则
- `architecture.md` - 技术架构快速参考
- `conventions.md` - 编码规范

**使用场景**：
- 新人入职时阅读（理解系统定位和约束）
- 开发前检查（是否违反铁律）
- 设计评审时参考（不可变约束）

**权威性**：
- 属于"治理冻结区"，变更需要充分理由
- 新增铁律必须有证据支持
- 修改铁律必须评估影响面

---

### 5. spec/ - 分阶段归档（版本演进）

**定位**：各阶段全量归档（v0.01-v0.06）

**目录结构**：
```
spec/
├── common/                     # 跨版本治理记录
│   └── records/
│       ├── development-status.md    # 开发状态
│       ├── debts.md                 # 技术债务
│       └── reusable-assets.md       # 可复用资产
│
└── v0.01-v0.06/               # 各版本目录
    ├── roadmap/               # 路线图与实现卡
    ├── evidence/              # 回测证据与验证记录
    ├── governance/            # 版本治理规则
    └── records/               # 版本记录与决策
```

**使用场景**：
- 查看版本路线图和实现进度
- 查阅回测证据和验证记录
- 追溯历史决策和变更记录

**维护规则**：
- 每个版本一个子目录
- 版本内按 roadmap/evidence/governance/records 组织
- common/records/ 存放跨版本记录

---

### 6. workflow/ - 工作流程（执行规范）

**定位**：定义标准工作流程

**核心文档**：
- `6A-WORKFLOW.md` - 标准 6A 工作流
  - A1 Align（对齐）
  - A2 Architect（拆解）
  - A3 Act（实施）
  - A4 Assert（验证）
  - A5 Archive（归档）
  - A6 Advance（同步）

**使用场景**：
- 每次任务开始前阅读 A1-A2
- 任务实施中遵循 A3-A4
- 任务完成后执行 A5-A6

**强制要求**：
- 未完成 A6 同步，不得宣告任务完成
- 未完成上一任务 A6，不得开始下一任务

---

### 7. reference/ - 参考资料（外部材料）

**定位**：外部参考资料，不作为执行口径

**核心文档**：
- `A股市场交易规则-tushare版.md`
- `A股涨跌停板制度-tushare版.md`
- `A股申万行业指数-tushare版.md`
- `temp-files-guide.md`

**使用场景**：
- 查阅 A 股市场规则
- 了解 TuShare API 规范
- 参考临时文件管理

---

## 🚀 快速导航

### 新人入职

1. **第一步**：阅读治理铁律
   - `steering/product.md` - 理解系统定位
   - `steering/a-stock-rules.md` - 理解 A 股约束
   - `steering/conventions.md` - 理解编码规范

2. **第二步**：阅读系统设计
   - `design-v2/system-baseline.md` - 系统基线
   - `design-v2/architecture-master.md` - 架构总览

3. **第三步**：阅读理论基础
   - `Strategy/README.md` - 理论总览
   - `Strategy/theoretical-foundations.md` - 理论溯源

4. **第四步**：阅读工作流程
   - `workflow/6A-WORKFLOW.md` - 标准工作流

### 开发任务

1. **任务开始前**：
   - 查阅 `design-v2/` 相关模块设计
   - 检查 `steering/` 是否违反铁律
   - 遵循 `workflow/6A-WORKFLOW.md` 执行 A1-A2

2. **任务实施中**：
   - 遵循 `design-v2/system-baseline.md` 执行语义
   - 参考 `Strategy/` 理论基础
   - 执行 A3-A4

3. **任务完成后**：
   - 使用 `observatory/sandbox-review-standard.md` 验证
   - 执行 A5-A6 归档同步
   - 更新 `spec/common/records/` 记录

### 版本规划

1. **规划阶段**：
   - 使用 `observatory/god-view-8-perspectives-v0.01.md` 全局审视
   - 参考 `spec/v0.0X/roadmap/` 历史路线图
   - 制定新版本路线图

2. **实施阶段**：
   - 遵循 `design-v2/system-baseline.md` 执行
   - 记录证据到 `spec/v0.0X/evidence/`
   - 更新进度到 `spec/v0.0X/roadmap/`

3. **验收阶段**：
   - 使用 `observatory/sandbox-review-standard.md` 评审
   - 归档记录到 `spec/v0.0X/records/`
   - 更新 `spec/common/records/development-status.md`

---

## 📋 文档维护规则

### 更新原则

1. **三大支柱**：
   - `design-v2/` - 设计变更需评估影响面
   - `observatory/` - 评审标准需保持稳定
   - `Strategy/` - 理论基础持续补充

2. **三大支撑**：
   - `steering/` - 铁律变更需充分理由
   - `spec/` - 按版本归档，不回溯修改
   - `workflow/` - 流程优化需团队共识

3. **参考资料**：
   - `reference/` - 及时更新外部材料

### 质量标准

1. **准确性**：内容准确，无歧义
2. **完整性**：覆盖核心内容，无遗漏
3. **一致性**：文档间引用正确，无冲突
4. **可追溯**：设计决策有理论依据或证据支持

### 冲突处理

若文档间存在冲突，优先级如下：

1. `design-v2/system-baseline.md` - 最高优先级
2. `steering/` - 不可变约束
3. `design-v2/` 其他文档 - 设计规范
4. `observatory/` - 验证标准
5. `Strategy/` - 理论参考
6. `spec/` - 历史记录
7. `reference/` - 外部材料

---

## 🔗 相关文档

- 仓库根目录：`AGENTS.md` / `CLAUDE.md` - 代理工作规则
- 项目根目录：`README.md` - 项目总览
- 代码目录：`src/` - 源代码实现

---

**文档状态**：Active  
**维护责任**：项目负责人  
**更新频率**：重大变更时更新
