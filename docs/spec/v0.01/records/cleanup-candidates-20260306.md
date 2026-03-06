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
