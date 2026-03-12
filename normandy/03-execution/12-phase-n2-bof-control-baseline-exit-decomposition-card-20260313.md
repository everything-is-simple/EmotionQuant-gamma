# Phase N2 BOF Control Baseline Exit Decomposition Card

**状态**: `Active`  
**日期**: `2026-03-13`  
**对象**: `N2 baseline diagnosis lane around BOF_CONTROL`

---

## 1. 定位

`N2 baseline lane` 不是把任何 retained branch 变相升格为新 baseline，也不是给 `FB_BOUNDARY / BOF_KEYLEVEL_PINBAR` 补开后门。

它只回答：

`在 BOF_CONTROL 已经被证明是当前唯一稳定 raw alpha baseline 的前提下，现有统一 Broker 出场语义到底吞掉了它多少 edge；问题主要是出在 exit damage，还是 execution friction。`

也就是说：

1. 这张卡只服务 `baseline diagnosis`
2. 不服务 `branch promotion`
3. `promotion lane` 继续保持锁住

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/01-full-design/01-alpha-first-mainline-charter-20260312.md`
3. `normandy/02-implementation-spec/01-alpha-provenance-and-exit-decomposition-spec-20260311.md`
4. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
5. `normandy/03-execution/records/10-phase-n1-12-bof-pinbar-stability-or-no-go-record-20260313.md`
6. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

---

## 3. 当前目标

`N2 baseline lane` 当前只做三件事：

1. 固定 `BOF_CONTROL` 为唯一 entry set，不再混入任何新 detector / quality branch
2. 在同一批 `BOF_CONTROL` entry 上拆解当前 exit 语义造成的收益损耗
3. 正式回答：
   - 当前问题更偏 `买错`
   - 还是更偏 `卖坏`

---

## 4. 固定研究对象

`N2 baseline lane` 当前固定只围绕：

1. `BOF_CONTROL`
2. 当前 `broker-frozen` 默认 exit 语义
3. 必要时加入少量可解释的对照 exit 变体

硬约束：

1. 不引入 `FB / SB / Tachibana / Volman deferred queue` 作为本卡比较对象
2. 不把 `BOF_KEYLEVEL_PINBAR / BOF_KEYLEVEL_STRICT / BOF_PINBAR_EXPRESSION` 拉回本卡
3. 不把 `IRS / MSS` 拉回本卡
4. 不借本卡直接改写当前主线默认运行口径

---

## 5. 固定执行约束

本卡固定约束为：

1. `signal set` 固定来自 `BOF_CONTROL`
2. 入场语义固定为现有 `T+1 Open`
3. 若比较多个 exit 方案，只允许改变 exit layer，不允许回头改 entry layer
4. `promotion lane` 当前继续锁住，不因本卡而自动放行
5. 所有新 exit 变体都必须是可解释、可复核的受控变体，不能写成曲线贴合补丁

---

## 6. 任务拆解

### N2-A Baseline Entry Freeze

目标：

1. 冻结 `BOF_CONTROL` 的 entry universe、trade lifecycle 与当前 control exit
2. 明确本轮允许比较的 exit dimensions
3. 写清哪些维度属于：
   - `exit damage`
   - `execution friction`
   - 非本卡范围

### N2-B Exit Damage Matrix

目标：

1. 在同一批 `BOF_CONTROL` entry 上运行受控 exit matrix
2. 输出至少以下证据：
   - `matrix summary`
   - `exit attribution`
   - `path digest`
3. 明确当前 edge 在哪些 exit 环节被吃掉最多

### N2-C Formal Readout

目标：

1. 正式回答 `BOF_CONTROL` 当前更像：
   - `entry mostly right but exit too harmful`
   - `entry edge limited and exit not main culprit`
   - `execution friction still material`
2. 给出后续治理动作：
   - 继续深挖 `exit decomposition`
   - 或回到 entry / backlog 队列
3. 保持 `promotion lane` 与 `baseline diagnosis lane` 的口径分离

---

## 7. 建议脚本入口

当前仓库还没有现成的 `Normandy N2 baseline lane` 专用脚本。

本卡当前建议入口为：

1. 复用 `scripts/backtest/run_normandy_pas_alpha_matrix.py` 的 entry freeze 口径作为上游参考
2. 复用 `scripts/backtest/run_v001_plus_trade_attribution.py` 的 attribution 结构作为对照参考
3. 若正式开跑，本卡应新增：
   - `scripts/backtest/run_normandy_bof_control_exit_matrix.py`
   - `scripts/backtest/run_normandy_bof_control_exit_digest.py`

也就是说：

`这张卡先把 baseline lane 的治理口径和执行边界写死，再决定脚本实现。`

---

## 8. 出场条件

`N2 baseline lane` 只有在以下条件全部成立时才允许出场：

1. 已固定 `BOF_CONTROL` 的 baseline entry freeze
2. 已形成 `exit attribution + path digest + matrix summary`
3. 已正式回答当前 `BOF_CONTROL` 的主要伤害是 `买错` 还是 `卖坏`
4. 已写明这不会自动解锁任何 `promotion lane`

---

## 9. 当前一句话任务

`不要再等小分支先过稳定性门槛；先把 BOF_CONTROL 这批已经站住的 entry 拆开，正式回答 exit 到底吞掉了多少 alpha。`
