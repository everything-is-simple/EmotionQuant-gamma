# design-v2 退场清单

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `docs/design-v2/ 作为 v0.01 historical baseline bundle 的保留、降级与未来删除边界`

---

## 1. 定位

本文不是删除命令，也不是新版设计文。

它只做一件事：

`把 docs/design-v2/ 剩余文件按“必须保留 / 可继续降级 / 未来可删除”三栏固定下来。`

从这一版起，`docs/design-v2/` 的角色正式压成：

`v0.01 historical baseline bundle`

也就是说：

1. 它不是当前系统设计层
2. 它不是当前治理层
3. 它只保留历史基线、历史总览和少量仍被依赖的冻结模块文

---

## 2. 判定规则

当前分类固定按下面四条判断：

1. 仍是历史权威口径、机器检查锚点或跨仓库入口锚点的文件，归入 `必须保留`
2. 仍被 `blueprint/` 当前正文直接吸收为历史设计原子的文件，归入 `必须保留`
3. 只剩历史 `v0.01` 规格/roadmap 引用，或只剩“未来第二批吸收对象”角色的文件，归入 `可继续降级`
4. 只有在“当前引用链已切断 + 上游吸收已完成 + 检查脚本已改写”三条件同时成立时，文件才允许进入 `未来可删除`

---

## 3. 当前分类

### 3.1 必须保留

| 文件 | 当前角色 | 保留原因 |
|---|---|---|
| `docs/design-v2/README.md` | 历史基线包入口 | 目录仍保留，就必须保留入口与边界声明，防止被误当成现行设计层。 |
| `docs/design-v2/01-system/system-baseline.md` | `v0.01 Frozen` 历史权威文件 | 仍被 `AGENTS / README / workflow / docs/spec / check_doc_authority.ps1` 等大量入口直接引用。 |
| `docs/design-v2/01-system/architecture-master.md` | 历史系统总览 | 仍被 `system-baseline.md`、`v0.01` roadmap/spec/release 和历史模块文依赖。 |
| `docs/design-v2/02-modules/selector-design.md` | `Selector / IRS-lite` 历史模块原子 | 当前仍被 `blueprint/01-full-design/01-*`、`03-*` 与相关 closure record 直接引用。 |
| `docs/design-v2/02-modules/strategy-design.md` | `PAS` 历史模块原子 | 当前仍被 `blueprint/01-full-design/02-*`、`06-*` 与相关 closure record 直接引用。 |
| `docs/design-v2/02-modules/broker-design.md` | `MSS-lite / Broker` 历史模块原子 | 当前仍被 `blueprint/01-full-design/04-*`、`05-*` 与相关 closure record 直接引用。 |

### 3.2 可继续降级

| 文件 | 当前角色 | 降级条件与方向 |
|---|---|---|
| `docs/design-v2/02-modules/data-layer-design.md` | `v0.01` 历史 Data 设计文 | 当前主要服务 `v0.01` roadmap/spec 与 `reusable-assets`；待 `blueprint` 或新的历史原子账本把 Data 核心设计收回后，可进一步降级。 |
| `docs/design-v2/02-modules/backtest-report-design.md` | `v0.01` 历史 Backtest/Report 设计文 | 当前主要服务 `v0.01` roadmap/spec 与后续“第二批对象整理”；待 `Backtest / Report` 在 `blueprint` 中独立收口后，可进一步降级。 |

### 3.3 未来可删除

当前这一栏固定为：

`空`

原因不是保守，而是当前 `docs/design-v2/` 剩余文件仍全部存在正式引用链。

换句话说：

`2026-03-12` 这一天，design-v2 可以继续瘦，但还没有任何一个文件达到“今天就能删”的条件。

---

## 4. 退场顺序

若后续继续瘦身，顺序固定建议为：

1. 先处理 `data-layer-design.md`
2. 再处理 `backtest-report-design.md`
3. 再处理 `selector / strategy / broker-design.md`
4. `architecture-master.md` 最后处理
5. `system-baseline.md` 作为最后一层历史权威锚点，原则上最后退场，甚至长期保留

这个顺序的原因是：

1. `Data / Backtest` 当前已不在现行主线五对象的第一吸收批次里
2. `Selector / Strategy / Broker` 还直接支撑 `blueprint` annex
3. `architecture-master` 仍是 `system-baseline` 的历史总览依赖
4. `system-baseline` 仍是整个历史线的唯一权威锚点

---

## 5. 当前允许动作

对 `docs/design-v2/`，当前只允许下面这些动作：

1. 维护入口、链接、边界说明
2. 补充退场清单、历史说明和只读导航
3. 在 `blueprint` 吸收完成后，更新某个文件的分类
4. 做受控归档，不做静默删除

当前明确不允许：

1. 在 `docs/design-v2/` 新增新版设计正文
2. 把当前主线设计重新写回这里
3. 在未切断引用链前删除文件
4. 用“目录太老了”作为删除理由

---

## 6. 一句话裁决

`docs/design-v2/` 现在还有必要，但只作为历史基线包保留；它只能继续冻结和瘦身，不能再被当成当前系统设计层。`
