# Report Scripts

**状态**: `Active`  
**日期**: `2026-03-18`

---

## 1. 目录职责

`scripts/report/` 放的是“专项报告/证据导出脚本”。

这层脚本的定位是：

1. 从现有执行库、raw 库或 evidence 表中抽取专题读数。
2. 生成 `json/csv/md` 等可落盘报告材料。
3. 服务某一张 card、record 或专项审计。

这层脚本不是：

1. 日常数据维护入口。
2. 默认回测入口。
3. 主系统运行入口。

---

## 2. 当前脚本

| 脚本 | 作用 | 主要输入 | 主要输出 |
|---|---|---|---|
| `build_g6_asof_evidence.py` | 构建第四战场 `G6` 的 as-of 覆盖率证据，核对 `raw_stock_basic -> l1_stock_info` 的新鲜度与命中情况 | raw 库、执行库 | `docs/spec/v0.01/*.json` evidence |

---

## 3. 使用原则

1. 先确认对应 card / record 需要什么证据，再运行脚本。
2. 输出路径尽量落到对应战场的 `evidence/` 或 `docs/spec/.../evidence/`。
3. 不要把这里的脚本误当成日更工具或回测 runner。

---

## 4. 推荐阅读顺序

1. 先看本目录 README。
2. 再看对应脚本的参数说明和头部注释。
3. 最后看脚本输出要落到哪张 card / record。

---

## 5. 一句话结论

`scripts/report/` 是“专项报告导出层”，负责把某个问题的证据抽出来，不负责日常维护和主线运行。
