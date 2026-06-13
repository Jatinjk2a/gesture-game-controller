import cv2
import time
from typing import List, Optional

_FONT = cv2.FONT_HERSHEY_SIMPLEX

# Zone highlight colours (BGR)
_ZONE_COLOR = {
    "JUMP":    (0, 255, 200),
    "DUCK":    (0, 200, 255),
    "LEFT":    (255, 200, 0),
    "RIGHT":   (255, 200, 0),
    "NEUTRAL": (0, 200, 0),
}

# Label positions as (col, row) → (label, relative-x, relative-y)
_GRID_LABELS = [
    (1, 0, "JUMP",    0.500, 0.160),
    (1, 2, "DUCK",    0.500, 0.840),
    (0, 1, "LEFT",    0.160, 0.500),
    (2, 1, "RIGHT",   0.840, 0.500),
    (1, 1, "NEUTRAL", 0.500, 0.500),
]


class HUD:
    def __init__(self):
        self._fps_stamps: List[float] = []
        self._flash_text: Optional[str] = None
        self._flash_at: float = 0.0

    # -----------------------------------------------------------------------
    # Grid
    # -----------------------------------------------------------------------

    def draw_grid(self, frame) -> None:
        h, w = frame.shape[:2]
        cw, rh = w // 3, h // 3
        clr = (0, 160, 0)
        for x in (cw, cw * 2):
            cv2.line(frame, (x, 0), (x, h), clr, 1)
        for y in (rh, rh * 2):
            cv2.line(frame, (0, y), (w, y), clr, 1)

        for _, _, label, rx, ry in _GRID_LABELS:
            px = int(rx * w) - len(label) * 4
            py = int(ry * h) + 5
            lc = _ZONE_COLOR.get(label, (90, 90, 90))
            cv2.putText(frame, label, (px, py), _FONT, 0.31, lc, 1, cv2.LINE_AA)

    def highlight_zone(self, frame, zone: str) -> None:
        if zone in ("NONE", ""):
            return
        h, w = frame.shape[:2]
        cw, rh = w // 3, h // 3
        coords = {
            "JUMP":    (cw,    0,    cw * 2, rh),
            "DUCK":    (cw,    rh*2, cw * 2, h),
            "LEFT":    (0,     rh,   cw,     rh * 2),
            "RIGHT":   (cw*2,  rh,   w,      rh * 2),
            "NEUTRAL": (cw,    rh,   cw * 2, rh * 2),
        }
        if zone not in coords:
            return
        x1, y1, x2, y2 = coords[zone]
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), _ZONE_COLOR.get(zone, (255, 255, 0)), -1)
        cv2.addWeighted(overlay, 0.22, frame, 0.78, 0, frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), _ZONE_COLOR.get(zone, (255, 255, 0)), 2)

    # -----------------------------------------------------------------------
    # Fingertip indicator + cooldown ring
    # -----------------------------------------------------------------------

    def draw_finger(self, frame, px: int, py: int) -> None:
        cv2.circle(frame, (px, py), 13, (0, 255, 255), -1)
        cv2.circle(frame, (px, py), 15, (255, 255, 255), 2)

    def draw_cooldown_ring(self, frame, px: int, py: int, progress: float) -> None:
        """Arc around the fingertip showing cooldown state (green=ready, orange=cooling)."""
        angle = int(360 * min(1.0, progress))
        color = (0, 230, 0) if progress >= 1.0 else (0, 140, 255)
        if angle > 0:
            cv2.ellipse(frame, (px, py), (20, 20), -90, 0, angle, color, 2)

    # -----------------------------------------------------------------------
    # Action flash (big centred text on key press)
    # -----------------------------------------------------------------------

    def flash(self, text: str) -> None:
        self._flash_text = text
        self._flash_at   = time.time()

    def draw_flash(self, frame) -> None:
        if not self._flash_text:
            return
        elapsed = time.time() - self._flash_at
        duration = 0.55
        if elapsed > duration:
            self._flash_text = None
            return

        alpha = 1.0 - elapsed / duration
        h, w  = frame.shape[:2]
        text  = self._flash_text
        scale = 1.7
        thick = 3
        (tw, th), _ = cv2.getTextSize(text, _FONT, scale, thick)
        tx = (w - tw) // 2
        ty = h // 2 - 20

        overlay = frame.copy()
        pad = 18
        cv2.rectangle(overlay,
                      (tx - pad, ty - th - pad),
                      (tx + tw + pad, ty + pad),
                      (0, 0, 0), -1)
        cv2.addWeighted(overlay, alpha * 0.65, frame, 1 - alpha * 0.65, 0, frame)
        cv2.putText(frame, text, (tx, ty), _FONT, scale,
                    (0, 255, 120), thick, cv2.LINE_AA)

    # -----------------------------------------------------------------------
    # Status bar (bottom strip)
    # -----------------------------------------------------------------------

    def draw_status_bar(self, frame, game_name: str, zone: str,
                        gesture: str, last_action: Optional[str]) -> None:
        h, w  = frame.shape[:2]
        bar_h = 46
        fps   = self._get_fps()

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - bar_h), (w, h), (8, 8, 12), -1)
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)
        cv2.line(frame, (0, h - bar_h), (w, h - bar_h), (45, 45, 45), 1)

        # Game name
        cv2.putText(frame, game_name, (8, h - bar_h + 15),
                    _FONT, 0.44, (80, 180, 255), 1, cv2.LINE_AA)

        # Zone + gesture
        cv2.putText(frame, f"Zone:{zone}  Gesture:{gesture}",
                    (8, h - 7), _FONT, 0.36, (150, 150, 150), 1, cv2.LINE_AA)

        # FPS
        cv2.putText(frame, f"FPS:{fps:02d}", (w - 62, h - 7),
                    _FONT, 0.36, (100, 100, 100), 1, cv2.LINE_AA)

        # Last action
        if last_action:
            label = f">>> {last_action} <<<"
            cv2.putText(frame, label, (w - 175, h - bar_h + 15),
                        _FONT, 0.48, (0, 255, 100), 1, cv2.LINE_AA)

    # -----------------------------------------------------------------------
    # Controls legend (gesture → key mapping for gesture/hybrid modes)
    # -----------------------------------------------------------------------

    def draw_controls_legend(self, frame, controls: dict, mode: str) -> None:
        if mode == "zone":
            return
        h, w = frame.shape[:2]
        items = [(g, k) for g, k in controls.items()]
        lx    = w - 145
        ly    = 50
        bh    = 14 * len(items) + 22

        overlay = frame.copy()
        cv2.rectangle(overlay, (lx - 4, ly - 16), (w - 4, ly + bh), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

        cv2.putText(frame, "CONTROLS:", (lx, ly),
                    _FONT, 0.31, (180, 180, 180), 1, cv2.LINE_AA)
        for i, (gesture, key) in enumerate(items):
            cv2.putText(frame, f"{gesture} -> {key.upper()}",
                        (lx, ly + 14 + i * 14), _FONT, 0.28,
                        (130, 220, 130), 1, cv2.LINE_AA)

    # -----------------------------------------------------------------------
    # Tips (top-left corner)
    # -----------------------------------------------------------------------

    def draw_tips(self, frame, tips: List[str]) -> None:
        for i, tip in enumerate(tips[:3]):
            cv2.putText(frame, f"• {tip}", (8, 20 + i * 17),
                        _FONT, 0.31, (180, 180, 70), 1, cv2.LINE_AA)

    # -----------------------------------------------------------------------
    # No-hand warning
    # -----------------------------------------------------------------------

    def draw_no_hand(self, frame) -> None:
        h, w = frame.shape[:2]
        cv2.putText(frame, "Show your hand...",
                    (w // 2 - 80, h // 2 - 20),
                    _FONT, 0.65, (70, 70, 230), 2, cv2.LINE_AA)

    # -----------------------------------------------------------------------
    # Internal FPS counter
    # -----------------------------------------------------------------------

    def _get_fps(self) -> int:
        now = time.time()
        self._fps_stamps = [t for t in self._fps_stamps if now - t < 1.0]
        self._fps_stamps.append(now)
        return len(self._fps_stamps)
