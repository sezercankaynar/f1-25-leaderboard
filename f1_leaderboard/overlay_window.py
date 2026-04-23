"""Şeffaf, framesiz, üstte kalan, click-through overlay penceresi.

Planlama: .planning/02-architecture.md, .planning/04-ui-design.md
"""
from __future__ import annotations

from typing import Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from .leaderboard_widget import LeaderboardWidget
from .race_state import Snapshot


class OverlayWindow(QWidget):
    def __init__(
        self,
        layout: dict,
        theme: dict,
        teams: Dict[str, dict],
        compounds: Dict[str, dict],
    ) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        screen_w, screen_h = layout["resolution"]
        ox, oy = layout.get("screen_origin", [0, 0])
        self.setGeometry(ox, oy, screen_w, screen_h)

        self._leaderboard = LeaderboardWidget(
            layout, theme, teams, compounds, parent=self
        )
        lb_origin = layout["leaderboard"]["origin"]
        self._leaderboard.move(lb_origin[0], lb_origin[1])

    def apply_snapshot(self, snap: Snapshot) -> None:
        self._leaderboard.set_snapshot(snap)
