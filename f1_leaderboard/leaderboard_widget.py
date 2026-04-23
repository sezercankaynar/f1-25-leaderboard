"""F1 TV tarzı leaderboard widget (Faz 4 — rewrite).

Adım 4a: Row pipeline yeniden düzenlendi. Team bar opak olarak ilk çizilir;
zebra/player/pit overlay'leri yalnızca team bar'ın SAĞINDAKİ alana uygulanır.
Logo/sektör/gap kolonları sonraki alt-adımlarda eklenecek.
"""
from __future__ import annotations

from typing import Dict, Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPainterPath
from PyQt6.QtWidgets import QWidget

from .race_state import Driver, Snapshot


def _derive_abbr(name: str) -> str:
    name = name.strip()
    if not name:
        return "---"
    parts = name.split()
    base = parts[-1] if len(parts) > 1 else parts[0]
    return base[:3].upper()


class LeaderboardWidget(QWidget):
    def __init__(
        self,
        layout: dict,
        theme: dict,
        teams: Dict[str, dict],
        compounds: Dict[str, dict],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._teams = teams
        self._compounds = compounds
        self._snapshot: Optional[Snapshot] = None

        lb = layout["leaderboard"]
        w, h = lb["size"]
        self.setFixedSize(w, h)
        self._row_height = int(lb["row_height"])
        self._top_accent = int(lb.get("top_accent_height", 6))
        self._corner_radius = int(lb.get("corner_radius", 12))
        self._divider_h = int(lb.get("divider_height", 1))
        self._content_top = self._top_accent

        self._pos_col = lb["position_col"]
        self._team_bar = lb["team_bar"]
        self._logo_col = lb["logo_col"]
        self._name_col = lb["name_col"]
        self._sector_bars_cfg = lb["sector_bars"]
        self._gap_col = lb["gap_col"]
        self._tyre_badge_cfg = lb["tyre_badge"]
        self._tyre_lap_cfg = lb["tyre_lap_text"]

        ff = theme.get("font_family", "Arial")
        self._font_pos = QFont(ff, max(8, int(lb.get("font_pos_size", 30))), QFont.Weight.Bold)
        self._font_name = QFont(ff, max(8, int(lb.get("font_name_size", 26))), QFont.Weight.Bold)
        self._font_tyre = QFont(ff, max(8, int(lb.get("font_tyre_size", 16))), QFont.Weight.Black)
        self._font_lap = QFont(ff, max(8, int(lb.get("font_lap_size", 16))), QFont.Weight.Medium)
        self._font_gap = QFont(ff, max(8, int(lb.get("font_gap_size", 18))), QFont.Weight.Medium)

        self._bg = QColor(theme["background_color"])
        self._bg.setAlphaF(float(theme.get("background_alpha", 0.94)))
        self._row_alt = QColor("#FFFFFF")
        self._row_alt.setAlphaF(float(theme.get("row_alt_alpha", 0.05)))
        self._divider = QColor(theme.get("divider_color", "#182030"))
        self._top_accent_color = QColor(theme.get("top_accent_color", "#FFCC00"))

        self._text = QColor(theme["text_primary"])
        self._text_dim = QColor(theme.get("text_secondary", "#8A96A6"))
        self._player_hl = QColor(theme.get("player_highlight", "#FFEB3B"))
        self._player_hl.setAlphaF(0.18)
        self._pit_hl = QColor(theme.get("pit_highlight", "#FF9800"))
        self._pit_hl.setAlphaF(0.28)

        self._fallback_team = QColor("#607D8B")
        self._fallback_compound_bg = QColor("#37474F")
        self._fallback_compound_fg = QColor("#FFFFFF")
        self._leader_text = QColor("#000000")

    def set_snapshot(self, snap: Snapshot) -> None:
        self._snapshot = snap
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        p = QPainter(self)
        w, h = self.width(), self.height()

        r = self._corner_radius
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(w - r, 0)
        path.arcTo(w - 2 * r, 0, 2 * r, 2 * r, 90, -90)
        path.lineTo(w, h - r)
        path.arcTo(w - 2 * r, h - 2 * r, 2 * r, 2 * r, 0, -90)
        path.lineTo(0, h)
        path.closeSubpath()
        p.fillPath(path, self._bg)

        p.fillRect(QRectF(0, 0, w, self._top_accent), self._top_accent_color)

        drivers = (
            sorted(
                (d for d in self._snapshot.drivers if d.position > 0),
                key=lambda d: d.position,
            )
            if self._snapshot is not None
            else []
        )

        if not drivers:
            p.setPen(self._text)
            p.setFont(self._font_name)
            p.drawText(
                QRectF(0, self._content_top, w, h - self._content_top),
                Qt.AlignmentFlag.AlignCenter,
                "waiting for UDP…",
            )
            p.end()
            return

        player_idx = self._snapshot.player_car_index
        for row, d in enumerate(drivers):
            y = self._content_top + row * self._row_height
            self._draw_row(p, y, d, d.index == player_idx, row)

        p.end()

    def _draw_row(self, p: QPainter, y: int, d: Driver, is_player: bool, row_idx: int) -> None:
        w = self.width()
        rh = self._row_height

        team = self._teams.get(str(d.team_id))
        team_color = QColor(team["color"]) if team else self._fallback_team
        tb_x = int(self._team_bar["x"])
        tb_w = int(self._team_bar["width"])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(team_color)
        p.drawRect(QRectF(tb_x, y, tb_w, rh))

        overlay_x = tb_x + tb_w
        overlay_w = w - overlay_x

        if row_idx % 2 == 1:
            p.fillRect(QRectF(overlay_x, y, overlay_w, rh), self._row_alt)

        if d.pit_status > 0:
            p.fillRect(QRectF(overlay_x, y, overlay_w, rh), self._pit_hl)
        elif is_player:
            p.fillRect(QRectF(overlay_x, y, overlay_w, rh), self._player_hl)

        p.fillRect(
            QRectF(overlay_x, y + rh - self._divider_h, overlay_w, self._divider_h),
            self._divider,
        )

        self._draw_position(p, y, d)

        p.setPen(self._text)
        p.setFont(self._font_name)
        name_rect = QRectF(self._name_col["x"], y, self._name_col["width"], rh)
        p.drawText(
            name_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            _derive_abbr(d.name),
        )

        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._draw_tyre_badge(p, y, d)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self._draw_tyre_lap(p, y, d)

    def _draw_position(self, p: QPainter, y: int, d: Driver) -> None:
        rh = self._row_height
        px = int(self._pos_col["x"])
        pw = int(self._pos_col["width"])
        pos_rect = QRectF(px, y, pw, rh)

        if d.position == 1:
            inset = 10
            fill_rect = QRectF(px + 2, y + inset, pw - 4, rh - 2 * inset)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._top_accent_color)
            p.drawRect(fill_rect)
            p.setPen(self._leader_text)
        else:
            p.setPen(self._text)

        p.setFont(self._font_pos)
        p.drawText(pos_rect, Qt.AlignmentFlag.AlignCenter, str(d.position))

    def _draw_tyre_badge(self, p: QPainter, y: int, d: Driver) -> None:
        cfg = self._tyre_badge_cfg
        diam = int(cfg["diameter"])
        cx = int(cfg["x"])
        cy = y + (self._row_height - diam) // 2
        compound = self._compounds.get(str(d.visual_compound))
        if compound:
            bg = QColor(compound["bg"])
            fg = QColor(compound["fg"])
            code = compound["code"]
        else:
            bg, fg, code = self._fallback_compound_bg, self._fallback_compound_fg, "?"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawEllipse(QRectF(cx, cy, diam, diam))
        p.setPen(fg)
        p.setFont(self._font_tyre)
        p.drawText(QRectF(cx, cy, diam, diam), Qt.AlignmentFlag.AlignCenter, code)

    def _draw_tyre_lap(self, p: QPainter, y: int, d: Driver) -> None:
        cfg = self._tyre_lap_cfg
        rect = QRectF(int(cfg["x"]), y, int(cfg["width"]), self._row_height)
        p.setPen(self._text_dim)
        p.setFont(self._font_lap)
        p.drawText(
            rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f"L{d.tyre_age_laps}",
        )
