# Tests 目录规范（强制）

本仓库测试按 **类型 + 模块** 双维度组织：

- `tests/unit/<module>/`：单元测试（纯函数、单模块行为）
- `tests/integration/<module>/`：集成测试（跨模块调用链）
- `tests/patches/<module>/`：补丁/回归测试（历史缺陷防回退）

模块目录与 `src/` 对齐：`data / selector / strategy / broker / backtest / report / core`。

规则：

1. 新增或修改 `src/<module>/` 代码，必须在对应 `tests/.../<module>/` 放置测试。
2. 修复线上或评审发现的问题，必须新增 `tests/patches/<module>/test_*.py` 回归用例。
3. 测试命令统一 `pytest -q`，不得依赖手工修改 `PYTHONPATH`。
