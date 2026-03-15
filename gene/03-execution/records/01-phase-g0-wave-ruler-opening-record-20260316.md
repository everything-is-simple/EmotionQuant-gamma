# G0 记录: 历史波段标尺脚手架已落地

**状态**: `Active`  
**日期**: `2026-03-16`

---

## 1. 本轮落地内容

1. 第四战场 `gene/` 已正式开线
2. 个股历史波段对象层术语已冻结
3. DuckDB 已补 `l3_stock_gene / l3_gene_wave / l3_gene_event`
4. `build_l3()` 已接入 `compute_gene()`
5. 已补最小单元测试与 build 链接线回归测试

---

## 2. 当前实现口径

1. 价格来源固定为 `l2_stock_adj_daily`
2. `pivot` 采用第一版 5-bar confirmation scaffold
3. `wave` 以相邻反向 pivot 形成
4. `event` 以新高/新低刷新与 `2B` 失败检测形成
5. `snapshot` 输出自历史与横截面两套标尺

---

## 3. 当前限制

1. 这不是最终的趋势定义正典
2. 这不是交易信号模块
3. 这还没有进入 `MSS / IRS` 融合
4. 这还没有扩展到指数/行业层

---

## 4. 下一步

1. 校准 `pivot / 1-2-3 / 2B` 的更严格定义
2. 加入行业与指数的镜像标尺
3. 开始检验 `magnitude / duration / extreme_density` 的解释力排序
