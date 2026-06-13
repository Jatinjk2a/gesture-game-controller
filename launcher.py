"""OpenCV-based game selection menu."""
import cv2
import json
import os
import numpy as np
from typing import Optional

_FONT  = cv2.FONT_HERSHEY_SIMPLEX
_W, _H = 640, 510
_ITEM_H   = 64
_START_Y  = 112
_BG_COLOR = (12, 12, 18)
_ACCENT   = (0, 180, 100)

_MODE_COLORS = {
    "zone":    (30,  100, 200),
    "gesture": (130, 40,  190),
    "hybrid":  (170, 80,  20),
}


def _load_games() -> list:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["games"]


def _draw_menu(frame: np.ndarray, games: list, selected: int) -> None:
    frame[:] = _BG_COLOR

    # Header
    cv2.putText(frame, "GESTURE GAME CONTROLLER",
                (62, 44), _FONT, 0.85, (0, 200, 255), 2, cv2.LINE_AA)
    cv2.putText(frame,
                "W/S  or  Up/Down  to navigate    Enter  to play    Q  to quit",
                (22, 72), _FONT, 0.33, (110, 110, 110), 1, cv2.LINE_AA)
    cv2.line(frame, (0, 86), (_W, 86), (38, 38, 38), 1)

    for i, game in enumerate(games):
        y      = _START_Y + i * _ITEM_H
        is_sel = (i == selected)

        # Selected row background + border
        if is_sel:
            cv2.rectangle(frame, (8, y - 6), (_W - 8, y + _ITEM_H - 14),
                          (22, 52, 22), -1)
            cv2.rectangle(frame, (8, y - 6), (_W - 8, y + _ITEM_H - 14),
                          _ACCENT, 1)

        # Hotkey number
        cv2.putText(frame, str(i + 1), (12, y + 18),
                    _FONT, 0.36, (70, 70, 70), 1, cv2.LINE_AA)

        # Game name
        name_clr = (0, 255, 120) if is_sel else (195, 195, 195)
        cv2.putText(frame, game["name"], (28, y + 19),
                    _FONT, 0.60, name_clr, 2 if is_sel else 1, cv2.LINE_AA)

        # First tip for selected row
        if is_sel and game.get("tips"):
            cv2.putText(frame, game["tips"][0], (28, y + 38),
                        _FONT, 0.30, (130, 195, 130), 1, cv2.LINE_AA)

        # Mode badge
        mode = game["control_mode"]
        bc   = _MODE_COLORS.get(mode, (70, 70, 70))
        bx1, by1, bx2, by2 = _W - 108, y + 3, _W - 12, y + 22
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), bc, -1)
        cv2.putText(frame, mode.upper(), (bx1 + 5, by1 + 13),
                    _FONT, 0.30, (245, 245, 245), 1, cv2.LINE_AA)

    # Footer
    fy = _START_Y + len(games) * _ITEM_H + 6
    cv2.line(frame, (0, fy), (_W, fy), (38, 38, 38), 1)
    cv2.putText(frame,
                "ZONE = finger in grid region   GESTURE = hand shape   HYBRID = both",
                (20, fy + 17), _FONT, 0.30, (75, 75, 75), 1, cv2.LINE_AA)
    cv2.putText(frame,
                "In controller:  Q = quit   C = toggle tips   1-6 = quick select",
                (20, fy + 32), _FONT, 0.30, (75, 75, 75), 1, cv2.LINE_AA)


def run_menu() -> Optional[dict]:
    """Display game selection menu. Returns the chosen game dict, or None if cancelled."""
    games    = _load_games()
    selected = 0
    frame    = np.zeros((_H, _W, 3), dtype=np.uint8)

    win = "Gesture Controller  —  Select a Game"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, _W, _H)

    while True:
        _draw_menu(frame, games, selected)
        cv2.imshow(win, frame)

        raw = cv2.waitKey(50)
        k   = raw & 0xFF

        # Quit / cancel
        if k in (ord("q"), 27):
            break

        # Confirm selection
        elif k in (13, 10):   # Enter
            cv2.destroyAllWindows()
            return games[selected]

        # Navigate up  (W or Up-arrow — Windows raw codes vary by backend)
        elif k == ord("w") or raw in (82, 65362, 2490368, -2621440):
            selected = (selected - 1) % len(games)

        # Navigate down  (S or Down-arrow)
        elif k == ord("s") or raw in (84, 65364, 2621440, -2490368):
            selected = (selected + 1) % len(games)

        # Quick-select by number key
        elif ord("1") <= k <= ord("6"):
            idx = k - ord("1")
            if idx < len(games):
                cv2.destroyAllWindows()
                return games[idx]

    cv2.destroyAllWindows()
    return None
