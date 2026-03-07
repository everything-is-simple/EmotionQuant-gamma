# EmotionQuant 6A-WORKFLOW（正式版）

**版本**: v1.2  
**状态**: Active（正式治理基线）  
**最后更新**: 2026-03-02  
**来源**: `docs/reference/workflows/6A工作流.md`（索引）

---

## 1. 适用范围

- 适用于本仓库所有开发任务（代码、文档、配置、脚本）。
- 执行目标：每次任务必须形成 `run/test/artifact/review/sync` 可复核闭环。
- 与系统设计关系：若与 `docs/design-v2/system-baseline.md` 冲突，以设计 SoT 为准。

## 2. 核心铁律（执行层）

1. 一次任务只允许 1 个主目标。
2. 任务必须可验收：至少一个可运行命令、一个可复现证据。
3. 未完成 A6 同步，不得宣告任务完成。
4. 记录文件不是可选项：每次任务都必须复核 `docs/spec/common/records/*`。
5. 未完成“上一任务 A6 同步”，不得开始下一任务。
6. 禁止“最后才补记录”：每完成一个子项，至少同步一次 `spec-*.md` 勾选进度（任务收口再执行完整 A6）。

---

## 3. 标准 6A

### A1 Align（对齐）

- 明确目标、范围、输入输出、风险。
- 挂接路线图位置（`docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md` + 对应 `v0.01-mvp-spec-*.md`）。
- 开工前硬门控（强制）：
  1. 确认上一任务已完成 A6（`development-status.md` §5 有记录）；未完成则先补齐再开工。
  2. 在 `development-status.md` §4.2 “进行中任务”新增本任务一行（任务/开始日期/状态/阻塞）。
- 产出：任务目标与边界说明（可在任务说明或 review 中）。

### A2 Architect（拆解）

- 拆成 1-3 个可交付子项。
- 明确验收口径：`run/test/artifact` 各是什么。
- 若涉及契约/风控/执行语义变更，先声明影响面。

### A3 Act（实施）

- 仅实现当前子项，避免超范围扩散。
- 涉及核心模块改动时，保持与 SoT 一致（BOF/T+1/契约边界等）。

### A4 Assert（验证）

- 运行命令成功（run）。
- 自动化测试通过或说明未跑原因（test）。
- 产物可检查（artifact）。
- 记录偏差、风险、降级方案（review）。

### A5 Archive（归档）

- 总结本次变更、风险、遗留事项。
- 新增遗留问题必须登记到 `debts.md`。
- 新增可复用方法/模板/脚本必须评估是否登记到 `reusable-assets.md`。

### A6 Advance（同步）

- 同步最小集合（强制）：
  1. `docs/spec/common/records/development-status.md`
  2. `docs/spec/common/records/debts.md`
  3. `docs/spec/common/records/reusable-assets.md`
  4. `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`（阶段状态）
  5. 对应 `docs/spec/v0.01/roadmap/v0.01-mvp-spec-*.md`（任务勾选/进度）
- 如果其中某项“无变化”，也必须在 `development-status.md` 的任务收口记录中写明 `N/A + 原因`。
- 同步完成后，才允许将任务状态标记为 `done` 或切换到下一个任务。

---

## 4. 任务完成判定（DoD）

以下任一不满足，任务状态只能是 `in_progress`：

- 无 run 证据
- 无 test 结果（或无未执行说明）
- 无 artifact 路径
- 无 review 结论
- 无 A6 同步记录

---

## 5. A6 同步检查清单（每次任务必填）

A6 同步的目的：防遗忘、可追溯、可复盘。完成 A6 前，任务不得标记为 done。

最小检查清单（强制）：

1. `docs/spec/common/records/development-status.md`
   - §4.2：本任务状态从进行中移除/标记完成
   - §5：追加 A6 收口一行（必选）
2. `docs/spec/common/records/debts.md`：新增债务则登记；无则写 `debts=无变化`
3. `docs/spec/common/records/reusable-assets.md`：新增资产则登记；无则写 `assets=无变化`
4. `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`：更新对应周次状态（TODO/IN_PROGRESS/DONE）
5. 对应 `docs/spec/v0.01/roadmap/v0.01-mvp-spec-*.md`：勾选本次完成项

A6 收口行模板（粘贴到 `development-status.md` §5）：

```md
| YYYY-MM-DD | 任务名 | pass/fail | pass/fail | 产物路径 | review路径 | debts/status/assets/roadmap/spec 已同步（或 N/A+原因） |
```

---

## 6. 严格模式触发条件

满足任一条件，升级为 Strict 6A（增加审查深度）：

1. Broker 风控逻辑调整
2. 执行语义或交易规则调整（T+1、涨跌停、费用模型）
3. 模块契约字段变更
4. 数据层 schema 变更

Strict 模式附加要求：

- 必须补充回归测试。
- 必须更新 `debts.md`（即使为“无新增债务”也要记录复核结果）。

## 7. 条件评审闸门（借鉴 RIPER-5）

以下任务在 A4 后必须增加一次“条件评审”再进入 A5/A6：

1. 修改 Broker 风控、交易执行、费用模型
2. 修改模块契约字段或语义
3. 修改主数据表 schema 或关键数据口径
4. 修改 SoT 设计总纲

评审最小结论模板：

```md
- 变更范围:
- 兼容性影响:
- 回归结果:
- 是否允许进入 A5/A6: yes/no
```

---

## 8. 两套工作流取舍

`docs/reference/workflows` 中两份文件的定位：

1. `6A工作流.md`：项目执行主流程（索引入口）。
2. `RIPER-5_With_Conditional_Review_Gate_CN.md`：外部方法参考，不作为主流程。

本项目最终口径：

- 主流程固定采用 6A。
- RIPER-5 只保留“条件评审闸门”思想，作为 6A 的附加门控，不单独运行。

---

## 9. 版本记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-03-02 | v1.2 | 强化执行约束：A1 开工门控 + 子项进度同步要求 + A6 同步检查清单 |
| 2026-03-02 | v1.1 | 新增“先同步后开新任务”硬约束 + 条件评审闸门 + 两套工作流取舍说明 |
| 2026-03-02 | v1.0 | 正式版重启：迁移到 `.kiro` 路径，纳入 record 三件套 + roadmap/spec 强制同步 |




