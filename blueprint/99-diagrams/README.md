# Blueprint Diagrams

**状态**: `Active`  
**日期**: `2026-03-09`

本目录保存 `blueprint` 当前主线的可打印架构图资产。

## 内容

1. `*.mmd`
   - Mermaid 源文件
2. `*.svg`
   - 矢量打印版
3. `*.png`
   - 位图打印版
4. `mermaid-config.json`
   - 统一渲染配置

## 当前图集

1. `eq-system-anatomy-20260309`
   - 当前要实现系统的大图
2. `eq-mainline-chain-comparison-20260309`
   - alpha / beta / frozen / current 主链路对照
3. `eq-mainline-evolution-20260309`
   - `v0.01 Frozen -> v0.01-plus -> blueprint` 演进图
4. `eq-contract-migration-20260309`
   - `StockCandidate / Signal / IndustryScore / MarketScore` 字段级迁移图

## 重渲染

使用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ops/render_blueprint_diagrams.ps1
```
