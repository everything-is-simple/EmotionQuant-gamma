# PAS 理论来源导航

**版本**：`PAS 理论参考入口`  
**状态**：`Active`  
**封版日期**：`不适用（Active）`  
**变更规则**：`允许补充来源索引、映射边界与勘误；不直接定义当前 PAS 执行口径。`

---

## 定位

`docs/Strategy/PAS/` 是 `PAS` 的共享理论来源层。

这里负责三件事：

1. 保留价格行为与形态框架的来源分析。
2. 保留 `Volman -> YTC -> A股日线` 的映射线索。
3. 说明哪些思想被当前主线吸收、哪些只保留为研究背景。

这里不是当前 `PAS` 设计 SoT。当前正式设计请看 `blueprint/01-full-design/`。

---

## 当前入口

| 文件 | 角色 |
|---|---|
| `lance-beggs-ytc-analysis.md` | `YTC` 五形态框架的一级来源说明 |
| `volman-ytc-mapping.md` | `Volman -> YTC -> A股` 的映射参考附录 |
| `xu-jiachong-naked-kline-analysis.md` | `BOF / Pin Bar` 的 A 股补充来源 |

---

## 使用边界

1. 这里说明来源、映射和采用边界，不定义 formal `Signal` 契约。
2. 这里可以保留研究性观察，但不再保留实现周计划、模块落点和代码草案。
3. 当前主线 `PAS` 的正式正文，以 `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md` 与 `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md` 为准。

---

## 相关文档

1. `docs/Strategy/README.md`
2. `docs/Strategy/theoretical-foundations.md`
3. `docs/design-v2/01-system/system-baseline.md`
4. `docs/spec/`
5. `docs/spec/common/records/development-status.md`
6. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
7. `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
