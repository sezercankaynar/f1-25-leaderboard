"""F1 brand logosunu (2018+ kırmızı 'F1' işareti) Wikimedia Commons'dan indir.

Çıktı: overlay/public/f1-logo.svg — Vite static asset olarak servis eder,
header.jsx içinden './f1-logo.svg' ile referans verilir.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "overlay" / "public" / "f1-logo.svg"

# 2018+ resmi F1 brand logosu — Wikimedia Commons (kamuya açık SVG)
URL = "https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg"
USER_AGENT = "Mozilla/5.0 (f1-leaderboard-overlay; logo-fetch)"


def main() -> int:
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as exc:
        print(f"[FAIL] download error: {exc}")
        return 1

    if not data.lstrip().startswith(b"<"):
        print(f"[FAIL] response is not SVG (size={len(data)}B)")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"[OK] {OUT} ({len(data)}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
