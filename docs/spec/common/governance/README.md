# common/governance 治理定义层

## 定位

`docs/spec/common/governance/` 存放跨版本、跨战场、跨实现周期都需要长期稳定维护的正式定义文件。

这里回答的是：

1. 系统有哪些统一术语
2. 哪些东西是对象，哪些只是指标或信号
3. 某些基础概念在系统内被正式定义为什么

这里不回答的是：

1. 某一阶段主线卡片如何推进
2. 某个研究窗口的临时结论
3. 单次实验的 evidence、record 或 patch 说明

## 与其他目录的边界

- `docs/spec/common/records/` 保存治理记录、状态账本、历史切换与证据索引
- `docs/spec/common/governance/` 保存正式定义、术语冻结稿与边界文件
- `blueprint/` 保存当前主线设计正文
- `normandy/`、`positioning/`、`gene/` 保存各战场专属研究正文

一句话：

`records` 记“发生了什么”，`governance` 定“系统里什么词是什么意思”。

## 当前入口

- `four-battlefields-unified-terminology-glossary-20260317.md`
- `four-battlefields-object-indicator-signal-boundary-20260317.md`
- `gene-foundational-definition-freeze-20260317.md`
- `normandy-foundational-definition-freeze-20260317.md`
- `positioning-foundational-definition-freeze-20260317.md`
- `gene-definition-gap-remediation-checklist-20260317.md`
- `research-line-promotion-discipline-freeze-20260318.md`

## 权威入口

- `../../../design-v2/01-system/system-baseline.md`
- `../records/development-status.md`

## 维护规则

1. 只有跨战场都要服从的定义，才进入这里。
2. 这里的文件必须尽量用稳定术语，不跟着单次实验结果漂移。
3. 若某个基础定义发生变更，必须能追溯到正式来源、设计边界和实现影响。
