"""Gesture recognition helpers: finger state detection, distances, and swipe detection."""

import math
import time
from collections import deque
from typing import Deque, List, Optional, Tuple

import config

# Landmark indices for fingertips and PIP (proximal interphalangeal) joints
TIP_IDS = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
PIP_IDS = [3, 6, 10, 14, 18]  # Joint below each tip


def calculate_distance(
    p1: Tuple[int, int], p2: Tuple[int, int]
) -> float:
    """Calculates Euclidean distance between two 2D points in pixel coordinates."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def count_fingers_up(
    landmarks: List[Tuple[int, int, int]], hand_label: Optional[str] = "Right"
) -> List[int]:
    """Determines which fingers are extended (up = 1, curled = 0).

    Args:
        landmarks: List of (id, x, y) tuples for 21 MediaPipe hand landmarks.
        hand_label: 'Right' or 'Left' handedness string.

    Returns:
        List of 5 integers [thumb, index, middle, ring, pinky] with 1 for extended, 0 for closed.
    """
    if len(landmarks) < 21:
        return [0, 0, 0, 0, 0]

    fingers: List[int] = []

    # 1. Thumb detection:
    # On a mirrored frame, for a Right hand facing the camera:
    # the thumb extends to the left (smaller X).
    # For a Left hand, it extends to the right (larger X).
    # We also verify distance to pinky base (landmark 17) for robust orientation.
    thumb_tip_x = landmarks[4][1]
    thumb_ip_x = landmarks[3][1]
    pinky_mcp_x = landmarks[17][1]

    # Geometric extension check: thumb tip is further from pinky MCP than IP joint
    thumb_dist_tip = abs(thumb_tip_x - pinky_mcp_x)
    thumb_dist_ip = abs(thumb_ip_x - pinky_mcp_x)

    if hand_label == "Left":
        is_thumb_extended = (thumb_tip_x > thumb_ip_x) or (thumb_dist_tip > thumb_dist_ip + 10)
    else:  # Default 'Right'
        is_thumb_extended = (thumb_tip_x < thumb_ip_x) or (thumb_dist_tip > thumb_dist_ip + 10)

    fingers.append(1 if is_thumb_extended else 0)

    # 2. Four Fingers (Index, Middle, Ring, Pinky):
    # In screen coordinates, Y decreases upwards (0 is top of image).
    # If tip Y is less than PIP Y, the finger is pointing up.
    for tip_id, pip_id in zip(TIP_IDS[1:], PIP_IDS[1:]):
        if landmarks[tip_id][2] < landmarks[pip_id][2]:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers


def classify_gesture(
    fingers: List[int],
    landmarks: List[Tuple[int, int, int]],
) -> str:
    """Classifies the raw gesture into one of the operational modes.

    Priority order:
    1. PAUSE: Fist (all fingers down, or all 4 fingers down).
    2. VOLUME: Thumb + Index pinch or extended while ring/pinky are closed.
    3. MOUSE: Index up only (or index+middle close for click within mouse mode).
    4. SLIDE: Index + Middle extended apart while ring/pinky closed.
    5. UNKNOWN: Hand visible but unclassified posture.

    Args:
        fingers: [thumb, index, middle, ring, pinky] flags (0 or 1).
        landmarks: 21 MediaPipe hand landmarks.

    Returns:
        Mode string: 'PAUSE', 'VOLUME', 'MOUSE', 'SLIDE', or 'UNKNOWN'.
    """
    if len(landmarks) < 21:
        return "UNKNOWN"

    thumb, index, middle, ring, pinky = fingers

    # 1. Closed Fist -> PAUSE mode (absolute priority)
    # If all fingers are closed or at least index, middle, ring, pinky are closed
    if (index == 0 and middle == 0 and ring == 0 and pinky == 0):
        return "PAUSE"

    # 2. Volume Mode: Thumb and Index up, ring and pinky curled down
    # Or pinch between thumb tip (4) and index tip (8)
    if thumb == 1 and index == 1 and ring == 0 and pinky == 0:
        return "VOLUME"

    # 3. Slide Mode: Index and Middle up, ring and pinky curled down,
    # with index tip (8) and middle tip (12) spread apart
    if index == 1 and middle == 1 and ring == 0 and pinky == 0:
        tip8 = (landmarks[8][1], landmarks[8][2])
        tip12 = (landmarks[12][1], landmarks[12][2])
        dist = calculate_distance(tip8, tip12)
        if dist >= config.CLICK_DISTANCE_THRESHOLD:
            return "SLIDE"
        else:
            # If fingers are close together, treat as MOUSE mode so user can trigger click
            return "MOUSE"

    # 4. Mouse Mode: Index finger up only (thumb may be curled or neutral)
    if index == 1 and middle == 0 and ring == 0 and pinky == 0:
        return "MOUSE"

    return "UNKNOWN"


class SwipeDetector:
    """Detects rapid horizontal hand swipe gestures over a sliding time window."""

    def __init__(
        self,
        history_duration: float = config.SWIPE_HISTORY_DURATION,
        min_displacement: float = config.SWIPE_MIN_DISPLACEMENT,
        cooldown: float = config.SLIDE_COOLDOWN,
    ) -> None:
        self.history_duration = history_duration
        self.min_displacement = min_displacement
        self.cooldown = cooldown
        self.history: Deque[Tuple[float, float]] = deque()  # (timestamp, x_pos)
        self.last_swipe_time: float = 0.0

    def update(
        self, x_pos: float, timestamp: Optional[float] = None
    ) -> Optional[str]:
        """Feeds the current hand x position and returns detected swipe direction.

        Args:
            x_pos: Horizontal position (e.g., wrist or index MCP) in pixels.
            timestamp: Optional explicit timestamp (uses time.time() if None).

        Returns:
            'RIGHT', 'LEFT', or None.
        """
        now = time.time() if timestamp is None else timestamp
        self.history.append((now, x_pos))

        # Evict records older than window duration
        while self.history and (now - self.history[0][0]) > self.history_duration:
            self.history.popleft()

        # Check cooldown
        if (now - self.last_swipe_time) < self.cooldown:
            return None

        if len(self.history) < 2:
            return None

        oldest_time, oldest_x = self.history[0]
        newest_time, newest_x = self.history[-1]
        dt = newest_time - oldest_time
        dx = newest_x - oldest_x

        if dt >= 0.02 and abs(dx) >= self.min_displacement:
            self.last_swipe_time = now
            self.history.clear()
            return "RIGHT" if dx > 0 else "LEFT"

        return None
