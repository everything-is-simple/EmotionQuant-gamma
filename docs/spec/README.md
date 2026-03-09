# Spec

## 定位

`docs/spec/` 是版本治理归档入口。

这里统一存放：

1. roadmap
2. governance
3. evidence
4. records

这里不再定义新版设计正文。

## 当前入口

| 入口 | 用途 |
|---|---|
| `common/records/development-status.md` | 当前治理状态与阶段判断 |
| `common/README.md` | 跨版本 common 层入口 |
| `v0.01/README.md` | `v0.01 Frozen` 历史版本材料 |
| `v0.01-plus/README.md` | 当前主线治理与证据入口 |

## 使用边界

1. 设计问题看 `blueprint/`。
2. 历史基线问题看 `docs/design-v2/`。
3. 版本证据、回顾、release、runbook 统一放 `docs/spec/<version>/`。

## 相邻入口

1. `common/records/development-status.md`
2. `../design-v2/01-system/system-baseline.md`
3. `../../blueprint/README.md`
