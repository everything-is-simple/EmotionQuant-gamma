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

## 3. 固定执行前提

除了 phase / card 顺序外，当前主线还固定继承一组非 phase 的执行前提：

1. 三目录纪律固定为：
   - `G:\EmotionQuant-gamma` 只放代码、文档、配置与脚本
   - `G:\EmotionQuant_data` 只放正式数据库、日志与长期数据产物
   - `G:\EmotionQuant-temp` 只放临时文件、工作副本、pytest / backtest / artifacts
2. 当前默认执行库固定为：
   - `G:\EmotionQuant_data\emotionquant.duckdb`
3. 当前默认旧库候选固定为：
   - `G:\EmotionQuant_data\duckdb\emotionquant.duckdb`
4. 当前补数顺序固定为：
   - 先复用本地旧库
   - 再用 TuShare 补缺
5. 当前 TuShare 固定按双通道角色执行：
   - `TUSHARE_PRIMARY_*` = `10000` 积分网关主通道
   - `TUSHARE_FALLBACK_*` = `5000` 积分官方兜底通道

上面这些前提的完整口径，统一固定在：

`blueprint/03-execution/00-current-dev-data-baseline-20260311.md`

后续 phase card 默认继承这份前提，不再每张卡重复重写。

---

## 4. 总执行顺序

当前顺序固定为：

1. `Phase 0 = P0 契约与 trace 收口`
2. `Phase 1 = P1 PAS 最小可交易形态层`
3. `Phase 1.5 = P1.5 主链稳定化收口`
4. `Phase 2 = P2 IRS 最小可交易排序层`
5. `Phase 3 = P3 MSS 最小可交易风控层`
6. `Phase 4 = P4 全链回归与 Gate 收口`

当前不允许跳步：

1. 不允许先改默认参数再补 trace
2. 不允许先跑大矩阵再补契约
3. 不允许同时并行改 `PAS / IRS / MSS` 三条主线

### 4.1 Phase 与 Full Design 绑定表

| Phase | 上游绑定 | 执行边界 |
|---|---|---|
| `Phase 0` | `01 / 02 / 03 / 04 / 05` | 只补 contract、trace、truth-source，不升级算法 |
| `Phase 1` | `02 + 06` | `02` 定 formal 边界，`06` 定 PAS 算法面 |
| `Phase 1.5` | `P0 + P1 + 09` | 只做稳定化收口，不升级算法正文 |
| `Phase 2` | `03 + 07` | `03` 定 contract 边界，`07` 定 IRS 算法面 |
| `Phase 3` | `04 + 08` | `04` 定 contract 边界，`08` 定 MSS 算法面 |
| `Phase 4` | `01-08` | 只重跑、归因、给出主线结论，不再改写正文 |

### 4.2 当前 Phase Card 入口

0. `非 phase 固定前提`
   - `blueprint/03-execution/00-current-dev-data-baseline-20260311.md`

1. `blueprint/03-execution/02-phase-0-contract-trace-card-20260309.md`
2. `blueprint/03-execution/03-phase-1-pas-card-20260309.md`
3. `blueprint/03-execution/03.5-phase-1.5-stabilization-card-20260310.md`
4. `blueprint/03-execution/04-phase-2-irs-card-20260309.md`
5. `blueprint/03-execution/05-phase-3-mss-card-20260309.md`
6. `blueprint/03-execution/06-phase-4-gate-card-20260309.md`

---

## 5. Phase 摘要

### 5.1 当前 6 张卡

1. `Phase 0`：
   - `blueprint/03-execution/02-phase-0-contract-trace-card-20260309.md`
2. `Phase 1`：
   - `blueprint/03-execution/03-phase-1-pas-card-20260309.md`
3. `Phase 1.5`：
   - `blueprint/03-execution/03.5-phase-1.5-stabilization-card-20260310.md`
4. `Phase 2`：
   - `blueprint/03-execution/04-phase-2-irs-card-20260309.md`
5. `Phase 3`：
   - `blueprint/03-execution/05-phase-3-mss-card-20260309.md`
6. `Phase 4`：
   - `blueprint/03-execution/06-phase-4-gate-card-20260309.md`

### 5.2 使用规则

1. 开工前先读对应 phase card。
2. 开工前还必须先读 `00-current-dev-data-baseline-20260311.md`，确认当前执行库、旧库候选、TuShare 双通道和目录纪律。
3. phase card 未出场，不进入下一张卡。
4. 总拆解文负责顺序和边界，phase card 负责 live checklist。

---

## 6. 每个 Phase 的统一交付模板

后续每推进一个 phase，都必须补齐下面 4 类内容：

### 6.1 代码

- [ ] 修改文件明确
- [ ] 新增文件明确
- [ ] 不改本 phase 非目标对象

### 6.2 测试

- [ ] 至少一组 unit test
- [ ] 必要时补 integration test
- [ ] 回归现有关键测试不破坏

### 6.3 Artifact / Evidence

- [ ] sidecar / trace / script 输出明确
- [ ] evidence json 落地
- [ ] records markdown 落地

### 6.4 治理同步

- [ ] `development-status.md` 同步进度
- [ ] `README / gate / roadmap` 如有必要同步
- [ ] docs gate 通过

---

## 7. 下一步

从 `2026-03-11` 起，`Phase 0`、`Phase 1`、`Phase 1.5` 与 `Phase 2` 都已完成出场，不再回到这些卡反复补散点。

先进入：

1. `Phase 3`
2. 以 `blueprint/03-execution/05-phase-3-mss-card-20260309.md` 为唯一开工卡

后续顺序固定为：

1. `Phase 3 / MSS`
2. `Phase 4 / Gate`

也就是：

`Phase 0 / Phase 1 / Phase 1.5 / Phase 2 已完成，下一步按 MSS -> Gate 顺序推进主线升级。`
