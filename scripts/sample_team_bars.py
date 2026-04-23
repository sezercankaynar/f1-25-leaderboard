"""Sample team color bar pixels from with_hud.png to diagnose the 'hepsi aynı renk' bug.

Reads the 4K overlay screenshot and averages a small RGB patch inside each row's
team bar (x in 20..30, within row bounds). Prints hex color per row so we can tell
whether colors are actually different (rendering working) or uniform (real bug).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG_PATH = ROOT / "with_hud.png"
OUT_CROP = ROOT / "with_hud_leaderboard_crop.png"

# layout.json base 4K
ORIGIN_X, ORIGIN_Y = 20, 200
WIDTH, HEIGHT = 360, 1600
ROW_HEIGHT = 80
TOP_ACCENT = 6
TEAM_BAR_X_IN = 2  # inside panel, after flush-left panel edge
TEAM_BAR_W = 10
ROW_COUNT = 20


def sample_color(img: Image.Image, x: int, y: int, w: int, h: int) -> tuple[int, int, int]:
    patch = img.crop((x, y, x + w, y + h))
    # mean RGB
    pixels = list(patch.getdata())
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)
    return r, g, b


def main() -> int:
    img = Image.open(IMG_PATH).convert("RGB")
    # Crop leaderboard area for visual inspection
    crop = img.crop((ORIGIN_X, ORIGIN_Y, ORIGIN_X + WIDTH, ORIGIN_Y + HEIGHT))
    crop.save(OUT_CROP)
    print(f"Saved crop: {OUT_CROP.name} ({crop.size})")

    print(f"\n{'row':>3} {'y_center':>8} {'hex':>8} {'r':>3} {'g':>3} {'b':>3}")
    seen = set()
    for row in range(ROW_COUNT):
        # row top within leaderboard panel
        row_top = TOP_ACCENT + row * ROW_HEIGHT
        # abs coords
        x = ORIGIN_X + TEAM_BAR_X_IN
        y = ORIGIN_Y + row_top + 20  # skip top padding, sample mid-row
        r, g, b = sample_color(img, x, y, TEAM_BAR_W - 2, 30)
        hx = f"#{r:02X}{g:02X}{b:02X}"
        seen.add(hx)
        print(f"{row+1:>3} {y:>8} {hx:>8} {r:>3} {g:>3} {b:>3}")

    print(f"\nDistinct colors sampled: {len(seen)}")
    if len(seen) <= 2:
        print("→ VERIFIED: team color bars are effectively uniform — bug is real.")
    else:
        print(f"→ Multiple distinct colors detected — bug may be perception-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
