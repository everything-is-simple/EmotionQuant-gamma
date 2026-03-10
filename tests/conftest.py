from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# 保证 `pytest` 直接执行时也能稳定导入仓库根目录下的 `src` 包。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import get_settings


def _configure_external_pytest_temp() -> Path:
    cfg = get_settings()
    pytest_root = (cfg.resolved_temp_path / "pytest").resolve()
    session_temp = pytest_root / "session-temp"
    session_temp.mkdir(parents=True, exist_ok=True)

    session_temp_str = str(session_temp)
    os.environ["TMP"] = session_temp_str
    os.environ["TEMP"] = session_temp_str
    os.environ["TMPDIR"] = session_temp_str
    return pytest_root


_PYTEST_TEMP_ROOT = _configure_external_pytest_temp()
# conftest 在收集阶段会提前触发一次 settings 解析；这里立刻清缓存，避免把那份实例带进测试体。
get_settings.cache_clear()


def pytest_configure(config) -> None:
    if getattr(config.option, "basetemp", None):
        return
    basetemp = _PYTEST_TEMP_ROOT / "basetemp"
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    config.option.basetemp = str(basetemp)


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    # 测试体内凡是走 get_settings() 的代码都应该拿到当前用例现场，而不是上个用例残留的单例。
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
