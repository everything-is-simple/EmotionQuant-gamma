# 第三战役：Normandy

## 战役定位

这里收 `Normandy` 这场研究战役的统一入口。

它不负责直接改写主线，只负责找 alpha、辨胜负、拆清 entry / exit / execution 的边界。

## 当前裁决

1. `BOF` 已固定为 `PAS raw alpha baseline / control`，不再作为待证对象。
2. `FB_BOUNDARY` 当前只保留为 `watch candidate / not-n2-ready`，不再占主队列第一优先级。
3. `SB` 当前 full detector 路线已正式 `no-go`，但保留 `SB_SMALL_W_MID_STRENGTH` 为窄 watch branch；`TACHI_CROWD_FAILURE` 当前固定为 `observation-only`。
4. `Normandy` 当前只负责找胜者，不负责直接宣布主线改写。

## 正式档案入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 研究线总入口 | `../../../normandy/README.md` | `Normandy` 的主入口 |
| 当前阶段结论 | `../../../normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md` | 当前对象分层、阶段裁决与优先级 |
| 研究资产层 | `../../../normandy/01-full-design/90-research-assets/README.md` | 当前研究线的对象定义、contract note、研究卡 |
| 研究线旧方案归档 | `../../../normandy/90-archive/README.md` | 研究线早期方案与已退场计划 |

## 已淘汰路线

1. 让 `Normandy` 直接宣布主线改写，绕开 `blueprint/` 和正式治理。
2. 继续围绕 `BPB` 当前 standalone detector 路线投入主队列资源。
3. 把 `RB_FAKE`、`PB / TST / CPB` 或当前 `TACHI_CROWD_FAILURE` 误写成已经胜出的第二 alpha。

## 下一步

1. 第一优先级固定为 `N1.11 / BOF pinbar quality provenance`。
2. 第二优先级固定为 `N1.12 / BOF family stability or no-go`。
3. `Tachibana` 当前只保留为延后 refinement / backlog；只有 `BOF family` 的 broker-frozen quality gate 跑完后，才允许回到这条线。

## 相邻入口

1. `docs/design-v2/01-system/system-baseline.md`
2. `docs/spec/common/records/development-status.md`
3. `docs/spec/`
