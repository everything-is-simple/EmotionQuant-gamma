# Current Mainline Execution Breakdown

**状态**: `Active`  
**日期**: `2026-03-08`  
**对象**: `当前主线执行拆解`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/01-full-design/01-selector-contract-annex-20260308.md`
3. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
4. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
5. `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
6. `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
7. `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
8. `blueprint/01-full-design/07-irs-minimal-tradable-design-20260309.md`
9. `blueprint/01-full-design/08-mss-minimal-tradable-design-20260309.md`
10. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
11. `docs/spec/common/records/development-status.md`

---

## 1. 定位

本文只做一件事：

`把唯一当前实现方案，拆成可以直接执行的 phase / task / checklist。`

它不回答设计是什么，也不重新定义实现目标。

它只回答：

1. 先做哪一包
2. 每包拆成哪些任务
3. 每个任务改哪些文件
4. 每包怎么验收和出场
5. 下一包什么时候允许开始

当前文档从现在起承担：

1. 总览
2. 顺序
3. phase 边界
4. phase card 入口

逐 phase 的 live checklist 不再继续堆在本文里。

---

## 2. 执行铁律

执行期固定遵守下面 6 条：

1. 只从 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` 往下拆。
2. 不允许在执行文里重新发明算法定义。
3. 每次只推进一个 `phase` 到“可验收”状态，再进入下一个。
4. 每个 `phase` 必须同时包含：
   - 代码落点
   - 测试落点
   - artifact 落点
   - done checklist
5. `legacy_bof_baseline` 必须始终保持可重跑。
6. 所有新增 trace / sidecar / artifact 都必须可通过 `run_id` 或 `signal_id` 回溯。
7. `P1 / P2 / P3` 执行前，必须同时检查对应 `contract annex + algorithm body`，不能只看 annex 开工。

---

## 3. 总执行顺序

当前顺序固定为：

1. `Phase 0 = P0 契约与 trace 收口`
2. `Phase 1 = P1 PAS 最小可交易形态层`
3. `Phase 2 = P2 IRS 最小可交易排序层`
4. `Phase 3 = P3 MSS 最小可交易风控层`
5. `Phase 4 = P4 全链回归与 Gate 收口`

当前不允许跳步：

1. 不允许先改默认参数再补 trace
2. 不允许先跑大矩阵再补契约
3. 不允许同时并行改 `PAS / IRS / MSS` 三条主线

### 3.1 Phase 与 Full Design 绑定表

| Phase | 上游绑定 | 执行边界 |
|---|---|---|
| `Phase 0` | `01 / 02 / 03 / 04 / 05` | 只补 contract、trace、truth-source，不升级算法 |
| `Phase 1` | `02 + 06` | `02` 定 formal 边界，`06` 定 PAS 算法面 |
| `Phase 2` | `03 + 07` | `03` 定 contract 边界，`07` 定 IRS 算法面 |
| `Phase 3` | `04 + 08` | `04` 定 contract 边界，`08` 定 MSS 算法面 |
| `Phase 4` | `01-08` | 只重跑、归因、给出主线结论，不再改写正文 |

### 3.2 当前 Phase Card 入口

1. `blueprint/03-execution/02-phase-0-contract-trace-card-20260309.md`
2. `blueprint/03-execution/03-phase-1-pas-card-20260309.md`
3. `blueprint/03-execution/04-phase-2-irs-card-20260309.md`
4. `blueprint/03-execution/05-phase-3-mss-card-20260309.md`
5. `blueprint/03-execution/06-phase-4-gate-card-20260309.md`

---

## 4. Phase 摘要

### 4.1 当前 5 张卡

1. `Phase 0`：
   - `blueprint/03-execution/02-phase-0-contract-trace-card-20260309.md`
2. `Phase 1`：
   - `blueprint/03-execution/03-phase-1-pas-card-20260309.md`
3. `Phase 2`：
   - `blueprint/03-execution/04-phase-2-irs-card-20260309.md`
4. `Phase 3`：
   - `blueprint/03-execution/05-phase-3-mss-card-20260309.md`
5. `Phase 4`：
   - `blueprint/03-execution/06-phase-4-gate-card-20260309.md`

### 4.2 使用规则

1. 开工前先读对应 phase card。
2. phase card 未出场，不进入下一张卡。
3. 总拆解文负责顺序和边界，phase card 负责 live checklist。

---

## 5. 每个 Phase 的统一交付模板

后续每推进一个 phase，都必须补齐下面 4 类内容：

### 5.1 代码

- [ ] 修改文件明确
- [ ] 新增文件明确
- [ ] 不改本 phase 非目标对象

### 5.2 测试

- [ ] 至少一组 unit test
- [ ] 必要时补 integration test
- [ ] 回归现有关键测试不破坏

### 5.3 Artifact / Evidence

- [ ] sidecar / trace / script 输出明确
- [ ] evidence json 落地
- [ ] records markdown 落地

### 5.4 治理同步

- [ ] `development-status.md` 同步进度
- [ ] `README / gate / roadmap` 如有必要同步
- [ ] docs gate 通过

---

## 6. 下一步

从本执行文生效起，下一步不再继续写新的执行散文。

直接进入：

1. `Phase 0`
2. 以 `blueprint/03-execution/02-phase-0-contract-trace-card-20260309.md` 为唯一开工卡

也就是：

`先把契约与 trace 收口做完，再谈 PAS / IRS / MSS 的升级。`
