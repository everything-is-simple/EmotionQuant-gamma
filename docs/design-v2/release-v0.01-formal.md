# EmotionQuant 系统文档封版记录（v0.01 正式版）

**版本**: v0.01 正式版  
**状态**: Frozen  
**封版日期**: 2026-03-03  
**说明**: 本记录用于声明 v0.01 系统文档已封版，作为后续迭代与回归比对基线。

## 1. 封版原则

1. `docs/design-v2/rebuild-v0.01.md` 为唯一执行口径（SoT）。
2. v0.01 封版后仅允许勘误、链接修复、非语义性排版调整。
3. 涉及执行语义、数据契约、风控规则、触发器定义的改动必须进入 v0.02+ 文档分支。

## 2. 本次封版覆盖文件

1. `README.md` / `README.en.md`
2. `AGENTS.md` / `AGENTS.en.md`
3. `CLAUDE.md` / `CLAUDE.en.md`
4. `WARP.md` / `WARP.en.md`
5. `docs/design-v2/rebuild-v0.01.md`
6. `docs/design-v2/architecture-master.md`
7. `docs/design-v2/data-layer-design.md`
8. `docs/design-v2/selector-design.md`
9. `docs/design-v2/strategy-design.md`
10. `docs/design-v2/broker-design.md`
11. `docs/design-v2/backtest-report-design.md`
12. `docs/design-v2/sandbox-review-standard.md`
13. `docs/design-v2/volman-ytc-mapping.md`

## 3. 后续版本约束

1. v0.02+ 新增能力不得回写覆盖 v0.01 封版语义。
2. 若需修正 v0.01 文档，只能以“勘误注记”方式追加，不得重写历史结论。
