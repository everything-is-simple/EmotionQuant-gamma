# 四战场文档书架

## 定位

这是一层非破坏式文档重组入口。

`blueprint/` 和 `docs/` 由于早期开发阶段没有完全按四战场切开，导致有些文档按“模块名”组织，有些按“版本”组织，有些按“历史阶段”组织。这个书架的作用，就是把这些旧入口重新按四战场视角整理一遍。

这里不移动原文档，只提供新的阅读路径。

## 入口

- `00-shared-and-history/README.md`
- `01-first-battlefield/README.md`
- `02-second-battlefield/README.md`
- `03-third-battlefield/README.md`
- `04-fourth-battlefield/README.md`

## 权威入口

- `../../design-v2/01-system/system-baseline.md`
- `../../spec/common/records/development-status.md`
- `../../spec/README.md`

## 使用方法

1. 先看你要解决的是哪一个战场的问题。
2. 再进入对应书架，顺着“正式入口 -> 历史补充 -> 边界文档”阅读。
3. 如果某份文档同时服务多个战场，则优先放入 `00-shared-and-history/`，避免重复归属。

## 当前归类原则

1. 第一战场收“运行骨架、主线设计、主线治理、默认运行手册”。
2. 第二战场收“alpha、setup、trigger、伤害诊断”。
3. 第三战场收“仓位、分批、退出、风险暴露”。
4. 第四战场收“趋势、波段、历史寿命、历史语境、镜像、条件层”。
5. 无法只归属一个战场的东西，进入共享与历史层。
