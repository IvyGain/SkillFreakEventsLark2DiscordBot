#!/usr/bin/env python3
"""
Lark to Discord Events Bot 実行スクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import run_bot

if __name__ == "__main__":
    run_bot()