# blueprint/01-full-design 归属说明

## 定位

`blueprint/01-full-design/` 是第一战场的正式设计正文层。

但由于主线是在早期模块化边界尚未完全清晰时逐步长出来的，这一层里有些文件虽然位于 `blueprint/`，语义上却分别对应第二、第三、第四战场的历史来源、主线吸收结果或跨战场共享定义。

所以阅读这里时，必须同时分清两件事：

1. 这些文件是否仍然属于当前主线 SoT
2. 这些文件的概念来源更接近哪一个战场

## 当前分层

### A. 第一战场核心正文

这些文件属于当前主线骨架，不应被重新归到其他战场：

- `01-selector-contract-annex-20260308.md`
- `02-pas-trigger-registry-contract-annex-20260308.md`
- `05-broker-risk-contract-annex-20260308.md`
- `09-mainline-system-operating-baseline-20260309.md`

### B. 主线吸收后的跨战场正文

这些文件虽然概念上分别来自第二、第三、第四战场，但在 `blueprint/` 中保留，是因为它们曾进入或影响过主线设计语言：

- `03-irs-lite-contract-annex-20260308.md`
- `04-mss-lite-contract-annex-20260308.md`
- `06-pas-minimal-tradable-design-20260309.md`
- `07-irs-minimal-tradable-design-20260309.md`
- `08-mss-minimal-tradable-design-20260309.md`

阅读口径：

1. 它们是“主线历史吸收结果”，不是今天各战场自己的最新 SoT。
2. 若要看第二、第三、第四战场今天各自怎么定义，优先回各战场目录。
3. 若要看它们何时、以什么边界被主线吸收或退役，再看 `docs/spec/v0.01-plus/records/`。

### C. 附录与共享参考

这些文件更适合视作共享与历史层，而不是主线正文：

- `90-design-source-register-appendix-20260309.md`
- `91-cross-version-object-mapping-reference-20260308.md`
- `92-mainline-design-atom-closure-record-20260308.md`

### D. 明显错层占位文件

- `10-stock-gene-library-design-20260313.md`

当前状态：

1. 该文件为空。
2. 语义上属于第四战场 `gene/`，不应继续被读者理解为第一战场正式正文。
3. 现阶段先保留原位，避免直接移动导致历史引用断裂；但在阅读上应视作“未完成的早期错层占位”，不纳入当前 SoT。

## 推荐阅读顺序

1. 先读 `01 / 02 / 05 / 09`
2. 再按需要回看 `03 / 04 / 06 / 07 / 08`
3. 最后才读 `90 / 91 / 92`
4. 不把 `10-stock-gene-library-design-20260313.md` 当正文使用
