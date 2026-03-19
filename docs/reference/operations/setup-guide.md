# EmotionQuant 环境配置指南

> 当前目录纪律：
> - `G:\EmotionQuant-gamma` 只放代码和文档
> - `G:\EmotionQuant_data` 只放数据库与日志
> - `G:\EmotionQuant-temp` 只放临时文件与运行时产物
> - `G:\EmotionQuant-report` 只放导出报表与人读报告

> 当前定位：
> - 本文是环境与运维参考，不是当前主线设计 SoT
> - 当前主线设计看 `blueprint/`
> - 当前状态看 `docs/spec/common/records/development-status.md`
> - 本文中的参数和值以示例为主，实际默认值以 `src/config.py` 与当前实现为准

本指南帮助你快速配置 EmotionQuant 的开发和运行环境。

---

## 📂 目录结构规划

### 推荐的四目录分离结构

```
G:\
├── EmotionQuant-gamma\          # 代码 + 文档（Git 仓库）
│   ├── src/                     # 源代码
│   ├── tests/                   # 测试
│   ├── docs/                    # 文档
│   ├── scripts/                 # 工具脚本
│   ├── .env                     # 环境变量配置（不提交真实值）
│   └── ...
│
├── EmotionQuant_data\           # 本地数据库（不进 Git）
│   ├── emotionquant.duckdb      # 主数据库
│   ├── emotionquant.duckdb-wal  # WAL 文件
│   ├── emotionquant.duckdb-shm  # 共享内存
│   └── logs/                    # 日志文件（可选）
│
├── EmotionQuant-temp\           # 临时文件（不进 Git）
    ├── logs/                    # 日志文件
    ├── cache/                   # 缓存
    ├── artifacts/               # 运行时产物
└── EmotionQuant-report\         # 导出报表（不进 Git）
    └── backtest_reports/        # 人读长报告 / 年报 / 导出表
```

**优势**：
- ✅ 代码与数据分离，便于备份和版本控制
- ✅ 数据库文件不会被误提交到 Git
- ✅ 临时文件独立管理，易于清理
- ✅ 多环境切换方便（开发/测试/生产）

---

## 🔧 快速配置步骤

### 步骤 1：创建数据目录

```powershell
# 创建数据目录
New-Item -ItemType Directory -Path "G:\EmotionQuant_data" -Force
New-Item -ItemType Directory -Path "G:\EmotionQuant_data\logs" -Force

# 创建临时目录
New-Item -ItemType Directory -Path "G:\EmotionQuant-temp" -Force
New-Item -ItemType Directory -Path "G:\EmotionQuant-temp\logs" -Force
New-Item -ItemType Directory -Path "G:\EmotionQuant-temp\cache" -Force
New-Item -ItemType Directory -Path "G:\EmotionQuant-temp\artifacts" -Force

# 创建报表目录
New-Item -ItemType Directory -Path "G:\EmotionQuant-report" -Force
New-Item -ItemType Directory -Path "G:\EmotionQuant-report\backtest_reports" -Force
```

### 步骤 2：配置 .env 文件

```powershell
# 复制环境变量模板
cd G:\EmotionQuant-gamma
Copy-Item .env.example .env

# 编辑 .env 文件
notepad .env
```

### 步骤 3：填写 .env 配置

打开 `.env` 文件，填写以下关键配置：

```bash
# ========================================
# 数据源配置
# ========================================
# TuShare API Token（必填）
TUSHARE_TOKEN=你的_TuShare_Token

# ========================================
# 数据路径配置（重要！）
# ========================================
# 数据根目录（指向外部数据目录）
DATA_PATH=G:\EmotionQuant_data

# 日志目录（可选，默认 ${DATA_PATH}/logs）
LOG_PATH=G:\EmotionQuant-temp\logs

# 原始 raw 历史库（可选）
# RAW_DB_PATH=G:\EmotionQuant_data\raw_history.duckdb

# ========================================
# 系统配置
# ========================================
# 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# 运行环境：development, production
ENVIRONMENT=development

# ========================================
# 主线模式示例（仅示例，实际以当前代码与 blueprint 为准）
# ========================================
PIPELINE_MODE=dtt
DTT_VARIANT=v0_01_dtt_bof_plus_irs_score

# ========================================
# 回测与交易参数
# ========================================
BACKTEST_INITIAL_CASH=1000000
COMMISSION_RATE=0.0003
MIN_COMMISSION=5.0
STAMP_DUTY_RATE=0.001
TRANSFER_FEE_RATE=0.00002
SLIPPAGE_BPS=0.001

STOP_LOSS_PCT=0.05
TRAILING_STOP_PCT=0.08
RISK_PER_TRADE_PCT=0.008
MAX_POSITION_PCT=0.10
MAX_POSITIONS=10

RISK_FREE_RATE=0.015

# ========================================
# Selector / Strategy 示例参数
# 实际默认值以 src/config.py 为准
# ========================================
MSS_VARIANT=zscore_weighted6
MSS_BULLISH_THRESHOLD=65
MSS_BEARISH_THRESHOLD=35
MIN_AMOUNT=50000
CANDIDATE_TOP_N=100
PRESELECT_SCORE_MODE=amount_plus_volume_ratio
```

---

## 📋 配置验证

### 验证目录结构

```powershell
# 检查数据目录
Test-Path "G:\EmotionQuant_data"
Test-Path "G:\EmotionQuant-temp"

# 检查 .env 文件
Test-Path "G:\EmotionQuant-gamma\.env"
```

### 验证环境变量

```powershell
# 进入项目目录
cd G:\EmotionQuant-gamma

# 安装依赖
pip install -e .

# 测试配置
python -c "from src.config import get_settings; cfg = get_settings(); print(f'DATA_PATH: {cfg.data_path}'); print(f'DB_PATH: {cfg.db_path}'); print(f'LOG_PATH: {cfg.log_path}')"
```

### 文件操作扩展环境

如果当前系统需要直接处理 `Word / Excel / PowerPoint / PDF / PS / TeX / DuckDB` 文件，额外安装：

```powershell
pip install -e .[fileops]
```

安装后可运行统一探针：

```powershell
python scripts/ops/file_ops_probe.py --output G:\EmotionQuant-temp\artifacts\file-ops-probe\probe-report.json
```

如果要彻底打通 `.ps` 与 `.tex`，还需要系统级工具：

1. `Ghostscript`：用于 `.ps/.eps` 渲染与转换
2. `MiKTeX` 或其他 TeX 发行版：用于 `.tex` 编译

探针会验证：

1. `docx / xlsx / pptx / pdf / duckdb` 的创建与回读
2. `ps` 的 Ghostscript 运行时是否就绪
3. `tex` 是否可编译成 PDF
4. `psd` 模块是否可用
5. Windows 下 `Word / Excel / PowerPoint / Acrobat` 的 COM 自动化入口是否存在

**预期输出**：
```
DATA_PATH: G:\EmotionQuant_data
DB_PATH: G:\EmotionQuant_data\emotionquant.duckdb
LOG_PATH: G:\EmotionQuant-temp\logs
```

---

## 🚀 开始使用

### 1. 拉取数据

```powershell
# 拉取交易日历和基础数据
python main.py fetch --start 2020-01-01 --end 2024-12-31
```

### 2. 构建数据层

```powershell
# 构建 L2 层（复权价、均线、量比等）
python main.py build --layers l2

# 构建 L3 层（MSS/IRS/PAS 算法输出）
python main.py build --layers l3

# 或一次性构建所有层
python main.py build --layers all
```

### 3. 运行回测（示例）

```powershell
# 运行回测
python main.py backtest --start 2020-01-01 --end 2024-12-31 --patterns bof

# 指定初始资金
python main.py backtest --start 2020-01-01 --end 2024-12-31 --patterns bof --cash 1000000
```

### 4. 日常运行（示例）

```powershell
# 运行今日全流程（fetch → build → selector → strategy → broker）
python main.py run

# 指定交易日期
python main.py run --trade-date 2024-12-31
```

---

## 📊 数据库文件说明

### DuckDB 文件

| 文件 | 说明 | 大小估算 |
|------|------|----------|
| `emotionquant.duckdb` | 主数据库文件 | 5-10 GB（5年数据） |
| `emotionquant.duckdb-wal` | Write-Ahead Log（写前日志） | 动态变化 |
| `emotionquant.duckdb-shm` | 共享内存文件 | 小文件 |

**注意**：
- WAL 和 SHM 文件在数据库关闭时会自动合并到主文件
- 不要手动删除 WAL 和 SHM 文件（可能导致数据丢失）
- 备份时只需备份 `.duckdb` 主文件

### 数据层级（L1-L4）

| 层级 | 内容 | 表前缀 |
|------|------|--------|
| L1 | 原始数据（API 直取） | `l1_*` |
| L2 | 加工数据（复权价/均线/量比） | `l2_*` |
| L3 | 算法输出（MSS/IRS/PAS） | `l3_*` |
| L4 | 历史分析缓存（订单/成交/报告） | `l4_*` |

---

## 🔒 安全建议

### 1. 保护敏感信息

```bash
# .env 文件已被 .gitignore 排除，不会提交到 Git
# 但仍需注意：
# - 不要在代码中硬编码 Token
# - 不要在日志中打印 Token
# - 不要在截图中暴露 Token
```

### 2. 备份策略

```powershell
# 定期备份数据库（建议每周）
Copy-Item "G:\EmotionQuant_data\emotionquant.duckdb" "G:\Backup\emotionquant_$(Get-Date -Format 'yyyyMMdd').duckdb"

# 备份配置文件
Copy-Item "G:\EmotionQuant-gamma\.env" "G:\Backup\.env_$(Get-Date -Format 'yyyyMMdd')"
```

### 3. 清理临时文件

```powershell
# 清理临时目录（释放磁盘空间）
Remove-Item "G:\EmotionQuant-temp\*" -Recurse -Force

# 或使用项目提供的清理脚本
powershell -ExecutionPolicy Bypass -File scripts/ops/clean_temp_files.ps1
```

---

## 🐛 常见问题

### Q1: 数据库文件找不到？

**A**: 检查 `.env` 文件中的 `DATA_PATH` 是否正确：

```powershell
# 检查配置
python -c "from src.config import get_settings; print(get_settings().db_path)"

# 检查目录是否存在
Test-Path "G:\EmotionQuant_data"
```

### Q2: TuShare API 调用失败？

**A**: 检查 Token 是否正确：

```powershell
# 测试 Token
python -c "import tushare as ts; ts.set_token('你的Token'); pro = ts.pro_api(); print(pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240131'))"
```

### Q3: 日志文件在哪里？

**A**: 日志文件位置由 `LOG_PATH` 决定：

```powershell
# 默认位置
G:\EmotionQuant-temp\logs\emotionquant.log

# 查看最新日志
Get-Content "G:\EmotionQuant-temp\logs\emotionquant.log" -Tail 50
```

### Q4: 如何切换环境（开发/生产）？

**A**: 修改 `.env` 文件中的 `ENVIRONMENT`：

```bash
# 开发环境（详细日志）
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# 生产环境（精简日志）
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Q5: 数据库太大，如何清理？

**A**: 删除不需要的历史数据前，先确认保留窗口、备份策略和当前主线证据需求：

```sql
-- 连接数据库
duckdb G:\EmotionQuant_data\emotionquant.duckdb

-- 删除旧数据（例如 2020 年之前）
DELETE FROM l1_stock_daily WHERE trade_date < '2020-01-01';
DELETE FROM l2_stock_daily WHERE trade_date < '2020-01-01';

-- 压缩数据库
VACUUM;
```

---

## 📚 相关文档

- 当前主线设计：`blueprint/README.md`
- 当前状态：`docs/spec/common/records/development-status.md`
- 历史基线：`docs/design-v2/01-system/system-baseline.md`
- 开发工作流：`docs/workflow/6A-WORKFLOW.md`
- 临时文件清理：见本文第 3 节与 `scripts/ops/clean_temp_files.ps1`

---

## ✅ 配置完成检查清单

- [ ] 创建 `G:\EmotionQuant_data` 目录
- [ ] 创建 `G:\EmotionQuant-temp` 目录
- [ ] 复制 `.env.example` 为 `.env`
- [ ] 填写 `TUSHARE_TOKEN`
- [ ] 设置 `DATA_PATH=G:\EmotionQuant_data`
- [ ] 设置 `LOG_PATH=G:\EmotionQuant-temp\logs`
- [ ] 安装依赖：`pip install -e .`
- [ ] 验证配置：运行配置测试命令
- [ ] 拉取数据：`python main.py fetch`
- [ ] 构建数据层：`python main.py build --layers all`
- [ ] 运行回测：`python main.py backtest`

---

**说明**：配置完成后，请先按当前 `blueprint` 主线和实际脚本入口选择运行方式，不要把本文示例误读为唯一正式流程。
