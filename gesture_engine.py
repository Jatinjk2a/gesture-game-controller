"""Hand gesture and zone detection using the mediapipe Tasks API (0.10+)."""
import os
import time
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision as mpv
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# ---------------------------------------------------------------------------
# Model – downloaded once to the project directory
# ---------------------------------------------------------------------------

_MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task"
)


def _ensure_model() -> None:
    if os.path.exists(_MODEL_PATH):
        return
    print("Downloading hand-landmark model (~8 MB) – one time only…")
    try:
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("Model saved to", _MODEL_PATH)
    except Exception as e:
        raise RuntimeError(f"Could not download model: {e}")


# ---------------------------------------------------------------------------
# Hand skeleton drawing (replaces the old drawing_utils)
# ---------------------------------------------------------------------------

_CONNECTIONS = [
    # thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # index
    (0, 5), (5, 6), (6, 7), (7, 8),
    # middle
    (5, 9), (9, 10), (10, 11), (11, 12),
    # ring
    (9, 13), (13, 14), (14, 15), (15, 16),
    # pinky
    (13, 17), (17, 18), (18, 19), (19, 20),
    # palm
    (0, 17), (0, 9),
]
_TIPS = {4, 8, 12, 16, 20}


def _draw_hand(frame, landmarks, w: int, h: int) -> None:
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in _CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 210, 0), 2)
    for i, (x, y) in enumerate(pts):
        color = (0, 120, 255) if i in _TIPS else (240, 240, 240)
        r = 6 if i in _TIPS else 4
        cv2.circle(frame, (x, y), r, color, -1)
        cv2.circle(frame, (x, y), r, (0, 0, 0), 1)


# ---------------------------------------------------------------------------
# Enums & data class
# ---------------------------------------------------------------------------

class Gesture(Enum):
    NONE        = "NONE"
    FIST        = "FIST"
    OPEN_PALM   = "OPEN_PALM"
    POINT       = "POINT"
    PEACE       = "PEACE"
    THUMBS_UP   = "THUMBS_UP"
    THUMBS_DOWN = "THUMBS_DOWN"
    ROCK        = "ROCK"


class Zone(Enum):
    NONE    = "NONE"
    NEUTRAL = "NEUTRAL"
    JUMP    = "JUMP"
    DUCK    = "DUCK"
    LEFT    = "LEFT"
    RIGHT   = "RIGHT"


@dataclass
class HandData:
    zone:       Zone
    gesture:    Gesture
    px:         int
    py:         int
    handedness: str
    landmarks:  list = field(repr=False)


# ---------------------------------------------------------------------------
# Gesture classification
# ---------------------------------------------------------------------------

def _fingers_up(lm) -> tuple:
    index      = lm[8].y  < lm[6].y
    middle     = lm[12].y < lm[10].y
    ring       = lm[16].y < lm[14].y
    pinky      = lm[20].y < lm[18].y
    thumb_high = lm[4].y  < lm[2].y
    return index, middle, ring, pinky, thumb_high


def _classify(lm) -> Gesture:
    index, middle, ring, pinky, thumb_high = _fingers_up(lm)
    main = (index, middle, ring, pinky)

    if not any(main):
        if thumb_high and lm[4].y < lm[0].y - 0.04:
            return Gesture.THUMBS_UP
        if not thumb_high and lm[4].y > lm[0].y + 0.04:
            return Gesture.THUMBS_DOWN
        return Gesture.FIST

    if all(main):
        return Gesture.OPEN_PALM
    if index and not middle and not ring and not pinky:
        return Gesture.POINT
    if index and middle and not ring and not pinky:
        return Gesture.PEACE
    if index and not middle and not ring and pinky:
        return Gesture.ROCK
    return Gesture.NONE


def _get_zone(px: int, py: int, w: int, h: int) -> Zone:
    col = min(2, max(0, int(px / (w / 3))))
    row = min(2, max(0, int(py / (h / 3))))
    if row == 1 and col == 1: return Zone.NEUTRAL
    if row == 0 and col == 1: return Zone.JUMP
    if row == 2 and col == 1: return Zone.DUCK
    if row == 1 and col == 0: return Zone.LEFT
    if row == 1 and col == 2: return Zone.RIGHT
    return Zone.NONE


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------

class GestureEngine:
    def __init__(self, max_hands: int = 1):
        _ensure_model()
        options = mpv.HandLandmarkerOptions(
            base_options=mpt.BaseOptions(model_asset_path=_MODEL_PATH),
            running_mode=mpv.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._lm = mpv.HandLandmarker.create_from_options(options)
        self._last: List[HandData] = []

    def process(self, rgb_frame, w: int, h: int) -> List[HandData]:
        """Detect hands and return structured results. rgb_frame must be uint8 RGB."""
        ts_ms = int(time.time() * 1000)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self._lm.detect_for_video(mp_img, ts_ms)

        out: List[HandData] = []
        if not result.hand_landmarks:
            self._last = out
            return out

        for i, landmarks in enumerate(result.hand_landmarks):
            tip = landmarks[8]
            px, py = int(tip.x * w), int(tip.y * h)
            label = "Right"
            if result.handedness and i < len(result.handedness):
                label = result.handedness[i][0].category_name
            out.append(HandData(
                zone=_get_zone(px, py, w, h),
                gesture=_classify(landmarks),
                px=px, py=py,
                handedness=label,
                landmarks=landmarks,
            ))

        self._last = out
        return out

    def draw(self, frame) -> None:
        """Draw hand skeletons for the most recent process() call."""
        h, w = frame.shape[:2]
        for hd in self._last:
            _draw_hand(frame, hd.landmarks, w, h)

    def close(self) -> None:
        self._lm.close()
