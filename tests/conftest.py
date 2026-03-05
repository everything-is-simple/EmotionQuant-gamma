from __future__ import annotations

import sys
from pathlib import Path

# 保证 `pytest` 直接执行时也能稳定导入仓库根目录下的 `src` 包。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
