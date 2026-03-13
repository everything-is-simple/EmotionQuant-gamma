# Sizing Lane Migration Boundary Table

**日期**: `2026-03-14`  
**阶段**: `Positioning / P5 handoff`  
**对象**: `sizing lane -> mainline / next lane migration boundary`  
**状态**: `Active`

---

## 1. 目标

本文只做一件事：

`把 sizing lane 当前哪些结论能迁、怎么迁、哪些不能迁写成一张边界表。`

---

## 2. Migration Boundary Table

| 对象 / 结论 | 当前裁决 | 是否依赖当前 full-exit semantics | 是否可迁回主线 | 当前允许的迁移方式 |
|---|---|---|---|---|
| `legacy_bof_baseline / no IRS / no MSS / current full-exit semantics` | `sizing frozen baseline` | `是` | `否` | 只作为第三战场 sizing/partial-exit 的研究输入，不改写主线默认运行口径 |
| `FIXED_NOTIONAL_CONTROL` | `canonical operating control baseline` | `部分依赖` | `可迁治理，不迁运行默认` | 迁到 `P6 / P7 / P8` 作为 operating control 设计基线，不升格为主线默认仓位 |
| `SINGLE_LOT_CONTROL` | `floor sanity control` | `部分依赖` | `可迁治理，不迁运行默认` | 迁到后续 lane 作为 floor sanity 尺子，不升格为主线默认仓位 |
| `WILLIAMS_FIXED_RISK / FIXED_RATIO` | `residual watch` | `是` | `否` | 只留研究线留档；若未来重开，必须以新 sizing hypothesis package 重新起证据链 |
| `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE` | `watch` | `是` | `否` | 只留研究线观察池，不进入主线，不进入 `P6` baseline |
| `FIXED_UNIT` | `no_go` | `是` | `可迁负面约束` | 可迁回治理层，写成“当前不再进入 active queue；若重开必须新假设，不做机械复跑” |
| `P2 provisional retained != retained` | `治理边界` | `否` | `是` | 迁回主线与研究线治理，防止把阶段性亮点误写成默认升级 |
| `single-lot sanity required before retained promotion` | `治理门槛` | `否` | `是` | 迁成跨 lane 的 retained promotion 前置门槛 |
| `residual watch != retained candidate` | `治理边界` | `否` | `是` | 迁成术语边界，禁止在 README / status / card 中口头升格 |
| `no retained sizing candidate => PX1 stays locked` | `治理边界` | `否` | `是` | 迁成条件卡开启规则，避免无 retained candidate 时提前做 cross-exit sensitivity |
| `partial-exit lane must not inherit sizing debt` | `治理边界` | `否` | `是` | 迁成 `P6` opening rule：不拿 residual watch / watch / no_go 当 partial-exit baseline |
| `当前没有 sizing formula 可迁回主线默认仓位` | `主结论` | `是` | `是` | 迁回主线治理层，写成“当前不切默认仓位”这一负面约束 |

---

## 3. 只对当前 Frozen Exit Semantics 成立的内容

当前必须继续留在研究线、不能外推为跨 exit 真理的内容固定为：

1. `no retained sizing candidate`
2. `WILLIAMS_FIXED_RISK / FIXED_RATIO = residual watch`
3. `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE = watch`
4. `FIXED_UNIT = no_go`

这些对象当前都没有通过：

`cross-exit sensitivity`

因此当前不能把它们翻译成：

`无论 exit 语义怎么改，这些结论都不会变。`

---

## 4. 可复用的跨 Lane 资产

当前可复用到 `partial-exit lane` 或迁回主线治理层的资产固定为：

1. `baseline freeze -> control matrix -> family replay -> retained-or-no-go -> closeout` 这条顺序
2. `operating control` 与 `floor sanity control` 双尺子结构
3. `retained`、`residual watch`、`watch`、`no_go` 的分层话语体系
4. `条件卡只在前置条件满足时打开` 的治理规则
5. `研究线升格靠 formal record，不靠口头结论` 的迁移纪律

---

## 5. 一句话结论

`P5` 的 migration boundary 很清楚：能迁的是治理边界和负面约束，不能迁的是任何当前仍受 frozen exit semantics 绑定的 sizing 公式身份。
