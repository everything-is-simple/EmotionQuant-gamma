# v0.01 目录清理候选（待确认）

**日期**: 2026-03-06  
**状态**: Confirmed and Applied  
**范围**: `docs/spec/v0.01/`

以下文件已按确认结果执行删除，保留本清单作为清理记录。

## 1. 明确重复

1. `docs/spec/v0.01/roadmap/v0.01-mvp.md`
   - 原因：与 `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md` 内容完全一致（同 SHA256）。
   - 处理：已删除，保留 `v0.01-mvp-roadmap.md` 作为唯一主入口。

## 2. 被最终版覆盖的证据文件

1. `docs/spec/v0.01/evidence/v0.01-bof-baseline-evidence-20260304.md`
   - 原因：为早期 `NO-GO` 证据，已被 `v0.01-bof-baseline-evidence-20260305.md` 覆盖。
   - 处理：已删除。
2. `docs/spec/v0.01/evidence/v0.01-g6-asof-evidence-20260305.json`
   - 原因：已被 `v0.01-g6-asof-evidence-20260305-v2.json` 覆盖。
   - 处理：已删除旧版，保留 `v2`。
3. `docs/spec/v0.01/evidence/v0.01-idempotency-check-20260305.json`
   - 原因：已被 `v0.01-idempotency-check-20260305-v4.json` 覆盖。
   - 处理：已删除旧版。
4. `docs/spec/v0.01/evidence/v0.01-idempotency-check-20260305-v2.json`
   - 原因：已被 `v0.01-idempotency-check-20260305-v4.json` 覆盖。
   - 处理：已删除旧版。
5. `docs/spec/v0.01/evidence/v0.01-idempotency-check-20260305-v3.json`
   - 原因：已被 `v0.01-idempotency-check-20260305-v4.json` 覆盖。
   - 处理：已删除旧版。

## 3. 中间态短跑证据

1. `docs/spec/v0.01/evidence/v0.01-idempotency-check-short-20260305.json`
2. `docs/spec/v0.01/evidence/v0.01-idempotency-check-short-20260305-v2.json`
3. `docs/spec/v0.01/evidence/v0.01-idempotency-check-short-20260305-v3.json`
   - 原因：均为短跑/中间验证产物，不是当前主证据链入口。
   - 处理：已统一删除。

## 4. 后续收口后清除的过时文件

1. `docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-20260306.json`
   - 原因：为 Week2 初轮分布审计，结论已被 `docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-20260306-v2.json` 覆盖。
   - 处理：已删除旧版，保留 `v2` 作为当前权威证据。
2. `docs/spec/v0.01/records/v0.01-algorithm-design-overview-20260306.md`
3. `docs/spec/v0.01/records/v0.01-algorithm-design-mss-20260306.md`
4. `docs/spec/v0.01/records/v0.01-algorithm-design-irs-20260306.md`
5. `docs/spec/v0.01/records/v0.01-algorithm-design-pas-20260306.md`
   - 原因：同日已正式迁入 `docs/design-v2/`，不再保留 `records` 中的中间草案副本。
   - 处理：已统一删除，算法 SoT 以 `docs/design-v2/*-algorithm.md` 为准。

## 5. 被更聚焦证据取代的中间实验产物

1. `docs/spec/v0.01/evidence/v0.01-selector-ablation-20260306.json`
2. `docs/spec/v0.01/evidence/v0.01-selector-ablation-gatemode-topn-short-20260306.json`
3. `docs/spec/v0.01/evidence/v0.01-selector-ablation-mss-ab-short-20260306.json`
4. `docs/spec/v0.01/evidence/v0.01-selector-ablation-mss-gatemode-ab-short-20260306.json`
   - 原因：均为 2026-03-06 当日的中间探索产物，已被更聚焦的 `v0.01-mss-variant-comparison-20260306.json` 与 `v0.01-selector-ablation-mss-fullcycle-ab-20260306.json` 覆盖。
   - 处理：已统一删除，仅保留当前可追溯且不互相打架的最终证据。

## 6. 二次收口（2026-03-06 晚）

1. `docs/spec/v0.01.tar`
2. `docs/spec/v0.01/evidence.tar`
   - 原因：均为人工导出的归档包，不属于当前 `docs/spec/v0.01/` 的正式执行/证据产物；保留在仓库树内有误提交风险。
   - 处理：已移出仓库工作树，不纳入版本控制。
3. `docs/spec/v0.01/evidence/v0.01-base-baseline-evidence-20260306.json`
   - 原因：为未正式纳管的 draft baseline 产物；当前 v0.01 已有历史 `GO baseline`、当前 full-cycle A/B 和证据总评审三层入口，继续保留该草稿会制造“当前正式 baseline 是否已封板”的歧义。
   - 处理：已删除草稿，不纳入当前正式证据链。
4. `docs/spec/v0.01/evidence/v0.01-evidence-review-20260306.md`
   - 原因：为本轮证据总评审汇总页，用于统一收口现有 `12` 份正式证据。
   - 处理：新增并保留，作为当前证据入口之一。
