import time
import pyautogui
from typing import Dict

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  # Remove the default 0.1 s delay between actions


class InputHandler:
    """Wraps pyautogui with per-key cooldown tracking."""

    def __init__(self, cooldown: float = 0.4):
        self.cooldown = cooldown
        self._last: Dict[str, float] = {}
        self._held: set = set()

    # ---- Press (tap) -------------------------------------------------------

    def press(self, key: str) -> bool:
        """Press a key if cooldown has elapsed. Returns True when a press fires."""
        now = time.time()
        if now - self._last.get(key, 0) >= self.cooldown:
            try:
                pyautogui.press(key)
                self._last[key] = now
                return True
            except Exception:
                pass
        return False

    # ---- Hold / release ----------------------------------------------------

    def hold(self, key: str) -> None:
        if key not in self._held:
            try:
                pyautogui.keyDown(key)
                self._held.add(key)
            except Exception:
                pass

    def release(self, key: str) -> None:
        if key in self._held:
            try:
                pyautogui.keyUp(key)
                self._held.discard(key)
            except Exception:
                pass

    def release_all(self) -> None:
        for key in list(self._held):
            try:
                pyautogui.keyUp(key)
            except Exception:
                pass
        self._held.clear()

    # ---- Cooldown introspection -------------------------------------------

    def ready(self, key: str) -> bool:
        return time.time() - self._last.get(key, 0) >= self.cooldown

    def progress(self, key: str) -> float:
        """0.0 = just pressed (full cooldown), 1.0 = ready to fire again."""
        elapsed = time.time() - self._last.get(key, 0)
        return min(1.0, elapsed / max(self.cooldown, 0.001))
