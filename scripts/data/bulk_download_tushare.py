#!/usr/bin/env python
from __future__ import annotations

"""TuShare 遗留批量下载入口。

当前定位不是每日主流程，而是 BaoStock 不可用时的保底入口。
真正的每日主流程已经切到本地 TDX 数据链。
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bulk_download import main


if __name__ == "__main__":
    raise SystemExit(main())
