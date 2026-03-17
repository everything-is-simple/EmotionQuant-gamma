# Strategy

**状态**: `Active`  
**定位**: `共享理论来源层`  
**维护规则**: `允许补充来源索引、映射边界与采用说明；不直接定义当前执行 SoT`

---

## 定位

`docs/Strategy/` 保留的是跨战场共享的理论来源、映射说明和采用边界。

这里回答的是：

1. 某些结构语言和市场语义从哪里来
2. 这些理论现在主要服务哪个战场
3. 哪些内容被系统吸收，哪些只保留为历史来源

这里不回答的是：

1. 当前默认 runtime 怎么跑
2. 当前主线参数如何冻结
3. 某条研究线今天的最新 SoT 是什么

这些内容应分别回：

- `blueprint/`
- `docs/spec/v0.01-plus/`
- `normandy/`
- `positioning/`
- `gene/`

## 当前主线口径

当前默认运行路径已经不再直接使用旧 `IRS / MSS` runtime 语义。

当前正式默认运行路径为：

`Selector 初选 -> BOF baseline entry -> FIXED_NOTIONAL_CONTROL -> FULL_EXIT_CONTROL -> Broker 执行`

因此，`Strategy/` 在今天的固定边界是：

1. `PAS` 提供第二战场与主线 `BOF` 的上游形态语言。
2. `IRS` 提供行业语义、历史接口和镜像参考，不再代表当前默认排序层。
3. `MSS` 提供市场环境历史语义和退役边界参考，不再代表当前默认控仓层。
4. `Strategy/` 只提供来源、映射、背景和共享经验补充，不直接充当执行 SoT。

## 四战场归属说明

### `PAS`

主要服务第二战场。

作用：

1. 给 `Normandy` 提供 setup / trigger 的上游理论语言。
2. 给主线 `BOF` 触发语义提供历史来源。

边界：

它不是第四战场的基础定义源。第四战场不能拿 `PAS` 代替“趋势 / 波段 / 寿命”的基本定义。

### `IRS`

今天更接近：

1. 第一战场的历史主线吸收遗产
2. 第四战场的行业镜像与历史语义参考

边界：

它不应再被理解为“当前主线默认排序层”。

### `MSS`

今天更接近：

1. 第一战场的历史市场语义遗产
2. 第四战场的市场环境参考和退役边界样本

边界：

它不应再被理解为“当前主线默认风险缩放层”。

## 当前结构

| 目录 | 角色 |
|---|---|
| `PAS/` | 价格行为与触发器语言来源 |
| `IRS/` | 行业口径与行业语义来源 |
| `MSS/` | 市场环境与情绪语义来源 |

## 阅读顺序

1. 先看本文件，确认来源边界。
2. 再按主题进入 `PAS / IRS / MSS`。
3. 需要看当前正式设计时，立即回 `blueprint/`。
4. 需要看当前治理状态时，回 `docs/spec/common/records/development-status.md`。

## 相关入口

1. `PAS/README.md`
2. `IRS/README.md`
3. `MSS/README.md`
4. `../navigation/four-battlefields-document-shelf/00-shared-and-history/cross-battlefield-document-classification-register-20260317.md`
5. `../../blueprint/README.md`
6. `../spec/common/records/development-status.md`
7. `../design-v2/01-system/system-baseline.md`
