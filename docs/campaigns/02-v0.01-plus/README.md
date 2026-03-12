# 第二战役：v0.01-plus

## 战役定位

这里收 `v0.01-plus` 这场主线战役的统一入口。

它已经把 `Selector -> PAS -> IRS -> MSS -> Broker` 这条链完整打过一遍，也已经经历了 `Phase 4 / Gate` 与 `Phase 4.1` 的正式裁决。

## 当前裁决

1. `v0.01-plus` 已完成整链验证，并且 `Phase 4 / Gate` 正式裁决为 `NO-GO`。
2. `Phase 4.1` 的 `carryover_buffer(1)` 与 `size_only_overlay` 都未推翻 `legacy_bof_baseline`。
3. 当前默认运行口径继续保持 `legacy_bof_baseline`；`v0.01-plus` 继续保留为主线治理与设计归档，不再靠局部微调强行翻案。

## 正式档案入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前设计 SoT | `../../../blueprint/README.md` | 当前主开发线设计正文 |
| 当前治理入口 | `../../spec/v0.01-plus/README.md` | `v0.01-plus` 的 governance / evidence / records |
| 战役后续废案归档 | `../../spec/v0.01-plus/90-archive/README.md` | 战役中产生但未采用的后续方案 |

## 已淘汰路线

1. 把 `v0_01_dtt_pattern_plus_irs_mss_score` 升为当前默认运行路径。
2. 继续沿 `Phase 4.1` 做 `MSS / Broker` 局部微调，伪造“已经翻盘”的结论。
3. 让研究线结论绕过正式 record 与 Gate replay，直接改写主线。

## 下一步

1. 设计正文继续以 `blueprint/` 为准，治理与证据继续归档到 `docs/spec/v0.01-plus/`。
2. 新的 alpha 答案先去 `Normandy` 研究线证明，再迁回主线。
3. 若未来要改写默认路径，必须重新满足：正式 record + direct Gate replay 打赢 `legacy_bof_baseline`。

## 相邻入口

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/spec/common/records/development-status.md`
3. `docs/spec/`
