# 路线图-设计桥接审查记录（2026-03-04）

**审查范围**:
- `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md` ~ `docs/spec/v0.06/roadmap/v0.06-portfolio.md`
- `docs/design-v2/architecture-master.md`、`docs/design-v2/backtest-report-design.md`、`docs/design-v2/broker-design.md`、`docs/design-v2/data-layer-design.md`、`docs/spec/v0.01/records/data-rebuild-runbook-20260303.md`、`docs/design-v2/system-baseline.md`、`docs/spec/v0.01/records/release-v0.01-formal.md`、`docs/design-v2/sandbox-review-standard.md`、`docs/design-v2/selector-design.md`、`docs/design-v2/strategy-design.md`、`docs/design-v2/volman-ytc-mapping.md`
- `docs/reference/未来之路/god_view_8_perspectives_report_v0.01.md`

**审查基线**:
- 执行口径：`docs/design-v2/system-baseline.md`
- 评审口径：`docs/design-v2/sandbox-review-standard.md`
- 未来规划附录：`docs/reference/未来之路/god_view_8_perspectives_report_v0.01.md`

## 1. 宏观层结论（目标与演进）

1. 版本演进主线（v0.01 -> v0.06）总体一致，未发现与 v0.01 冻结口径直接冲突的强约束违规。
2. 路线图与“八视角”映射基本成立，但原文存在局部口径漂移（见第 4 节）。
3. 审查前存在“桥接断点”：部分路线图链接到不存在的 spec 文件，已修复为 `docs/design-v2/*` 有效入口。

## 2. 系统层结论（门禁与可执行性）

1. 原路线图普遍只写 `S0/S1=0`，缺少七维证据、kill-chain 回放、幂等重跑等 Go/No-Go 必备证据落点。
2. 已在 v0.01-v0.06 路线图中补充统一门禁要求，使“能评审”从口号变为可执行清单。
3. v0.02-v0.06 均补充了“评审证据与 Go/No-Go 门禁（补充）”段，明确每版应提交的证据类型。

## 3. 分层结论（模块边界与时序）

1. 时序主线 `signal_date=T -> execute_date=T+1 -> price=T+1 Open` 仍保持一致。
2. v0.02 已补充 BPB 确认期与 T+1 语义关系，避免“确认期改写撮合语义”。
3. v0.06 已补充组合层并发冲突优先级，减少“组合风控与个股风控重复拒单/语义打架”风险。

## 4. 发现问题与修复（按严重度）

1. `S1`：v0.01 路线图引用不存在的 `spec-01~05` 文件，桥接失效。  
   修复：改为指向现有 `docs/design-v2/data-layer-design.md`、`selector-design.md`、`strategy-design.md`、`broker-design.md`、`backtest-report-design.md`。
2. `S1`：v0.02-v0.06 缺少定稿门禁证据落点（七维证据/kill-chain/幂等重跑/Go-No-Go）。  
   修复：逐文件新增“评审证据与 Go/No-Go 门禁（补充）”章节。
3. `S1`：v0.05 文档内自相矛盾（正文“自动禁用” vs 风险段“仅建议模式”）。  
   修复：统一为默认建议模式（`AUTO_ENV_DISABLE=False`），人工审核后启用。
4. `S2`：v0.04 引用视角三，但本版范围未落地 signal quality。  
   修复：引用改为视角二/五/六，并注明视角三在 v0.05 深化。
5. `S2`：v0.06 仓位描述逻辑不严谨（“取较小值”却写“R 风险下限保护”）。  
   修复：改为“R 风险硬上限约束”，并补充组合层冲突优先级。

## 5. 剩余风险（未在本轮改动）

1. `docs/design-v2/*` 为 v0.01 Frozen 文档；v0.02+ 的实现细节仍需在对应版本建立独立设计与实现卡，不能回写覆盖 v0.01 语义。
2. v0.03+ 的新增状态机（如 CriticalPointManager）后续需补充“状态可达性 + 时间推进”回归测试设计，否则在七维“状态机完整性”维度有潜在 `S1` 风险。

## 6. 本轮审查结论

1. 经过本轮修订，路线图作为“设计 -> 实现”桥接文档已从“可读”提升到“可执行、可审计、可回放”。
2. 结论：**可继续推进，但必须按新增门禁条目提交证据，否则不得晋级下一版本。**




