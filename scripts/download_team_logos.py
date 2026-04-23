"""Download 2025 F1 team logos from formula1.com CDN, convert to 64x64 PNG with transparency.

Saves to config/assets/teams/{teamId}.png where teamId matches config/teams.json.
"""

from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "config" / "assets" / "teams"

# teamId (matches config/teams.json) -> formula1.com CDN slug
TEAMS: dict[str, str] = {
    "0": "mercedes",
    "1": "ferrari",
    "2": "redbullracing",
    "3": "williams",
    "4": "astonmartin",
    "5": "alpine",
    "6": "racingbulls",
    "7": "haasf1team",
    "8": "mclaren",
    "9": "kicksauber",
}

URL_TMPL = (
    "https://media.formula1.com/image/upload/"
    "c_lfill,w_256/q_auto/v1740000001/common/f1/2025/{slug}/2025{slug}logowhite.webp"
)

TARGET_SIZE = (64, 64)
USER_AGENT = "Mozilla/5.0 (f1-leaderboard-overlay; logo-fetch)"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def process(team_id: str, slug: str) -> tuple[str, int]:
    url = URL_TMPL.format(slug=slug)
    data = fetch(url)
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    img.thumbnail(TARGET_SIZE, Image.LANCZOS)
    canvas = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
    x = (TARGET_SIZE[0] - img.width) // 2
    y = (TARGET_SIZE[1] - img.height) // 2
    canvas.paste(img, (x, y), img)
    out_path = OUT_DIR / f"{team_id}.png"
    canvas.save(out_path, "PNG", optimize=True)
    return str(out_path), out_path.stat().st_size


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[tuple[str, str, str]] = []
    for team_id, slug in TEAMS.items():
        try:
            path, size = process(team_id, slug)
            status = "OK" if size < 20_000 else "WARN>20KB"
            print(f"[{status}] id={team_id} slug={slug} size={size}B path={path}")
        except Exception as exc:
            failures.append((team_id, slug, repr(exc)))
            print(f"[FAIL] id={team_id} slug={slug} err={exc}")
    if failures:
        print(f"\n{len(failures)} download(s) failed.")
        return 1
    print("\nAll 10 logos downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
