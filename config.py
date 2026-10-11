"""Global configuration and tunable parameters for Hand Gesture Control."""

from typing import Tuple

# Camera Settings
CAMERA_INDEX: int = 0
FRAME_WIDTH: int = 640
FRAME_HEIGHT: int = 480
FPS_TARGET: int = 30

# MediaPipe Hands Settings
MP_MAX_NUM_HANDS: int = 1
MP_MIN_DETECTION_CONFIDENCE: float = 0.7
MP_MIN_TRACKING_CONFIDENCE: float = 0.7

# Mouse Control Settings
# Active zone margins inside the 640x480 frame
ACTIVE_ZONE_MARGIN_X: int = 100
ACTIVE_ZONE_MARGIN_Y: int = 80
MOUSE_SMOOTHENING: float = 5.0  # Formula: curr = prev + (target - prev) / smoothening

# Click Gesture Settings
# Distance in pixels between index (8) and middle (12) tips
CLICK_DISTANCE_THRESHOLD: float = 38.0
CLICK_COOLDOWN: float = 0.3  # Seconds between clicks

# Volume Control Settings
# Distance in pixels between thumb (4) and index (8) tips
PINCH_MIN_DIST: float = 25.0
PINCH_MAX_DIST: float = 160.0
VOLUME_SMOOTHENING: float = 3.0

# Slide Control Settings
SLIDE_COOLDOWN: float = 1.0  # Seconds between slide triggers
SWIPE_HISTORY_DURATION: float = 0.35  # Seconds of history to check for swipe
SWIPE_MIN_DISPLACEMENT: float = 130.0  # Minimum pixel delta across the window

# Mode Switching & Debouncing
MODE_DEBOUNCE_FRAMES: int = 3  # Consecutive frames needed to switch modes

# UI & Display Styling (BGR color tuples)
COLOR_TEXT: Tuple[int, int, int] = (255, 255, 255)
COLOR_TEXT_SHADOW: Tuple[int, int, int] = (0, 0, 0)
COLOR_ACTIVE_ZONE: Tuple[int, int, int] = (255, 140, 0)      # Neon Cyan/Blue in BGR
COLOR_MOUSE_MODE: Tuple[int, int, int] = (50, 220, 50)       # Green
COLOR_VOLUME_MODE: Tuple[int, int, int] = (255, 190, 0)      # Cyan/Yellow
COLOR_SLIDE_MODE: Tuple[int, int, int] = (220, 50, 220)      # Magenta
COLOR_PAUSE_MODE: Tuple[int, int, int] = (60, 60, 240)       # Red
COLOR_NO_HAND: Tuple[int, int, int] = (140, 140, 140)        # Gray
