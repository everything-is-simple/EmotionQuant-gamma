# 跨战场文档分类登记表

## 目的

这份登记表用来说明：

1. 哪些旧文档虽然位于 `blueprint/` 或 `docs/Strategy/`，但更适合按战场理解
2. 哪些文件应该继续保留在共享与历史层
3. 哪些文件现阶段先不移动，只在阅读口径上降级

## 一、blueprint/01-full-design

### 1. 继续视作第一战场核心正文

- `blueprint/01-full-design/01-selector-contract-annex-20260308.md`
- `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
- `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
- `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`

### 2. 视作“主线吸收后的跨战场正文”

- `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
- `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
- `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
- `blueprint/01-full-design/07-irs-minimal-tradable-design-20260309.md`
- `blueprint/01-full-design/08-mss-minimal-tradable-design-20260309.md`

### 3. 视作共享与历史层

- `blueprint/01-full-design/90-design-source-register-appendix-20260309.md`
- `blueprint/01-full-design/91-cross-version-object-mapping-reference-20260308.md`
- `blueprint/01-full-design/92-mainline-design-atom-closure-record-20260308.md`

### 4. 暂不移动但应降级的文件

- `blueprint/01-full-design/10-stock-gene-library-design-20260313.md`

原因：

1. 文件为空
2. 语义应属第四战场
3. 当前没有继续维护价值，不应再被理解成主线正文

## 二、docs/Strategy

### 1. 继续保留为共享理论源

- `docs/Strategy/PAS/`
- `docs/Strategy/IRS/`
- `docs/Strategy/MSS/`

### 2. 对四战场的实际服务关系

- `PAS`
  主要服务第二战场；第四战场可借用其结构语法做条件解释，但 `PAS` 本身不是第四战场定义源
- `IRS`
  今天更适合作为第四战场和主线历史语义参考；不再直接代表当前默认 runtime
- `MSS`
  今天更适合作为历史市场语义与环境治理参考；不再直接代表当前默认 runtime

## 三、当前整理策略

当前采用的是：

`先补分类口径，再补阅读入口，再决定是否移动少量低风险文件`
