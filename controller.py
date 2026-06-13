"""Main gesture controller loop for a selected game profile."""
import cv2
import webbrowser
import time
from typing import Optional

import pyautogui

from gesture_engine import GestureEngine, Zone, Gesture
from input_handler  import InputHandler
from hud            import HUD


# ---------------------------------------------------------------------------
# Action resolver
# ---------------------------------------------------------------------------

def _resolve(game: dict, zone: Zone, gesture: Gesture) -> Optional[str]:
    """Map current zone/gesture to a key string using the game's control profile."""
    mode     = game["control_mode"]
    controls = game["controls"]
    z        = zone.value
    g        = gesture.value

    if mode == "zone":
        if z not in ("NEUTRAL", "NONE") and z in controls:
            return controls[z]

    elif mode == "gesture":
        if g in controls:
            return controls[g]

    elif mode == "hybrid":
        # Gesture takes priority (attacks), then fall back to zone (movement)
        if g in controls:
            return controls[g]
        if z not in ("NEUTRAL", "NONE") and z in controls:
            return controls[z]

    return None


# ---------------------------------------------------------------------------
# Controller entry point
# ---------------------------------------------------------------------------

def run_controller(game: dict) -> None:
    engine  = GestureEngine(max_hands=game.get("max_hands", 1))
    handler = InputHandler(cooldown=game.get("cooldown", 0.4))
    hud     = HUD()
    mode    = game["control_mode"]

    # Open the game URL
    url = game.get("url", "")
    if url:
        print(f"Opening {game['name']} in browser...")
        webbrowser.open(url)

    for i in range(5, 0, -1):
        print(f"  Starting in {i}…")
        time.sleep(1)
    print(f"[{game['name']}] Controller active  —  Press Q to stop\n")

    # Open webcam (try indices 0-2)
    cap = None
    for idx in range(3):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            break
    if not cap or not cap.isOpened():
        print("Error: no webcam found.")
        engine.close()
        return

    TW, TH   = 640, 480          # processing resolution
    DW, DH   = 480, 360          # display window size
    sw, sh   = pyautogui.size()
    WIN      = f"Controller  [{game['name']}]"

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, DW, DH)
    cv2.moveWindow(WIN, sw - DW - 10, 10)   # top-right corner

    # Per-mode state
    zone_locked = False    # zone mode: require return to NEUTRAL before next press
    last_action: Optional[str] = None
    show_tips   = True

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.resize(frame, (TW, TH))
        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]

        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hands = engine.process(rgb, w, h)
        engine.draw(frame)

        hud.draw_grid(frame)

        cur_zone    = Zone.NONE
        cur_gesture = Gesture.NONE
        action_fired: Optional[str] = None

        if hands:
            hd          = hands[0]          # primary hand
            cur_zone    = hd.zone
            cur_gesture = hd.gesture

            hud.highlight_zone(frame, cur_zone.value)
            hud.draw_finger(frame, hd.px, hd.py)

            # Cooldown ring — use progress of the resolved key
            action_key = _resolve(game, cur_zone, cur_gesture)
            if action_key:
                prog = handler.progress(action_key)
                hud.draw_cooldown_ring(frame, hd.px, hd.py, prog)

            # Fire input
            if mode == "zone":
                if cur_zone == Zone.NEUTRAL:
                    zone_locked = False
                elif action_key and not zone_locked:
                    if handler.press(action_key):
                        action_fired = action_key.upper()
                        zone_locked  = True

            else:   # gesture / hybrid
                if action_key and handler.press(action_key):
                    action_fired = action_key.upper()

        else:
            hud.draw_no_hand(frame)

        if action_fired:
            last_action = action_fired
            hud.flash(action_fired)

        hud.draw_flash(frame)

        if show_tips:
            hud.draw_tips(frame, game.get("tips", []))

        hud.draw_controls_legend(frame, game["controls"], mode)
        hud.draw_status_bar(frame, game["name"],
                            cur_zone.value, cur_gesture.value, last_action)

        cv2.imshow(WIN, frame)

        k = cv2.waitKey(1) & 0xFF
        if k in (ord("q"), 27):
            break
        elif k == ord("c"):
            show_tips = not show_tips

    # Cleanup
    handler.release_all()
    engine.close()
    cap.release()
    cv2.destroyAllWindows()
    print(f"[{game['name']}] Controller stopped.")
