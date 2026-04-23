"""PyInstaller entry point — tek dosya exe için.

PyInstaller `-m` bayrağı kullanamaz, `.py` dosyası bekler. Bu dosya
f1_leaderboard paketini import edip app.main()'i çalıştırır. PyInstaller
bağımlılıkları otomatik tespit eder.
"""
from __future__ import annotations

import sys

from f1_leaderboard.app import main


if __name__ == "__main__":
    sys.exit(main())
