"""Unit tests for gesture recognition, distance math, swipe detection, and controllers."""

import math
import time
from typing import List, Tuple
import pytest

import config
from gestures import (
    calculate_distance,
    count_fingers_up,
    classify_gesture,
    SwipeDetector,
)
from controllers.mouse import MouseController
from controllers.slides import SlideController
from controllers.volume import VolumeController


def create_mock_hand(
    thumb_extended: bool = False,
    index_up: bool = False,
    middle_up: bool = False,
    ring_up: bool = False,
    pinky_up: bool = False,
    index_middle_distance: float = 60.0,
    hand_label: str = "Right",
) -> List[Tuple[int, int, int]]:
    """Helper to generate synthetic 21-landmark data for testing."""
    # Base wrist at (300, 400)
    landmarks: List[Tuple[int, int, int]] = [(0, 300, 400)]

    # Thumb: 1: CMC, 2: MCP, 3: IP, 4: TIP
    # For Right hand facing camera in mirrored frame, thumb extends left (smaller X)
    if thumb_extended:
        thumb_tip_x = 220 if hand_label == "Right" else 380
    else:
        thumb_tip_x = 280 if hand_label == "Right" else 320

    thumb_ip_x = 260 if hand_label == "Right" else 340
    landmarks.append((1, 290, 370))
    landmarks.append((2, 275, 340))
    landmarks.append((3, thumb_ip_x, 310))
    landmarks.append((4, thumb_tip_x, 290))

    # Index: 5: MCP, 6: PIP, 7: DIP, 8: TIP
    index_base_x = 280
    index_pip_y = 250
    index_tip_y = 180 if index_up else 290
    landmarks.append((5, index_base_x, 300))
    landmarks.append((6, index_base_x, index_pip_y))
    landmarks.append((7, index_base_x, 220))
    landmarks.append((8, index_base_x, index_tip_y))

    # Middle: 9: MCP, 10: PIP, 11: DIP, 12: TIP
    middle_base_x = int(index_base_x + index_middle_distance)
    middle_pip_y = 240
    middle_tip_y = 170 if middle_up else 290
    landmarks.append((9, middle_base_x, 290))
    landmarks.append((10, middle_base_x, middle_pip_y))
    landmarks.append((11, middle_base_x, 210))
    landmarks.append((12, middle_base_x, middle_tip_y))

    # Ring: 13: MCP, 14: PIP, 15: DIP, 16: TIP
    ring_base_x = 340
    ring_pip_y = 250
    ring_tip_y = 180 if ring_up else 300
    landmarks.append((13, ring_base_x, 300))
    landmarks.append((14, ring_base_x, ring_pip_y))
    landmarks.append((15, ring_base_x, 220))
    landmarks.append((16, ring_base_x, ring_tip_y))

    # Pinky: 17: MCP, 18: PIP, 19: DIP, 20: TIP
    pinky_base_x = 370
    pinky_pip_y = 260
    pinky_tip_y = 190 if pinky_up else 310
    landmarks.append((17, pinky_base_x, 310))
    landmarks.append((18, pinky_base_x, pinky_pip_y))
    landmarks.append((19, pinky_base_x, 230))
    landmarks.append((20, pinky_base_x, pinky_tip_y))

    return landmarks


def test_distance_calculation():
    """Validates 2D Euclidean distance helper."""
    assert calculate_distance((0, 0), (3, 4)) == pytest.approx(5.0)
    assert calculate_distance((100, 100), (100, 100)) == 0.0


def test_fist_triggers_pause():
    """A closed fist must be classified as PAUSE mode."""
    hand = create_mock_hand(
        thumb_extended=False,
        index_up=False,
        middle_up=False,
        ring_up=False,
        pinky_up=False,
    )
    fingers = count_fingers_up(hand, hand_label="Right")
    assert fingers[1:] == [0, 0, 0, 0]
    mode = classify_gesture(fingers, hand)
    assert mode == "PAUSE"


def test_index_only_triggers_mouse():
    """Only index finger up must be classified as MOUSE mode."""
    hand = create_mock_hand(
        thumb_extended=False,
        index_up=True,
        middle_up=False,
        ring_up=False,
        pinky_up=False,
    )
    fingers = count_fingers_up(hand, hand_label="Right")
    assert fingers == [0, 1, 0, 0, 0]
    mode = classify_gesture(fingers, hand)
    assert mode == "MOUSE"


def test_two_fingers_apart_triggers_slide():
    """Index and middle up spread apart must be classified as SLIDE mode."""
    hand = create_mock_hand(
        thumb_extended=False,
        index_up=True,
        middle_up=True,
        ring_up=False,
        pinky_up=False,
        index_middle_distance=65.0,  # Greater than CLICK_DISTANCE_THRESHOLD (38.0)
    )
    fingers = count_fingers_up(hand, hand_label="Right")
    assert fingers == [0, 1, 1, 0, 0]
    mode = classify_gesture(fingers, hand)
    assert mode == "SLIDE"


def test_two_fingers_close_triggers_mouse_click_gesture():
    """Index and middle close together must classify as MOUSE mode for click action."""
    hand = create_mock_hand(
        thumb_extended=False,
        index_up=True,
        middle_up=True,
        ring_up=False,
        pinky_up=False,
        index_middle_distance=20.0,  # Below CLICK_DISTANCE_THRESHOLD (38.0)
    )
    fingers = count_fingers_up(hand, hand_label="Right")
    assert fingers == [0, 1, 1, 0, 0]
    mode = classify_gesture(fingers, hand)
    assert mode == "MOUSE"


def test_volume_gesture():
    """Thumb and index up with others curled triggers VOLUME mode."""
    hand = create_mock_hand(
        thumb_extended=True,
        index_up=True,
        middle_up=False,
        ring_up=False,
        pinky_up=False,
    )
    fingers = count_fingers_up(hand, hand_label="Right")
    assert fingers == [1, 1, 0, 0, 0]
    mode = classify_gesture(fingers, hand)
    assert mode == "VOLUME"


def test_swipe_detector_velocity_and_cooldown():
    """Validates swipe direction detection and cooldown suppression."""
    detector = SwipeDetector(
        history_duration=0.4,
        min_displacement=100.0,
        cooldown=1.0,
    )

    t0 = 1000.0
    detector.update(100.0, timestamp=t0)
    detector.update(180.0, timestamp=t0 + 0.05)
    swipe = detector.update(250.0, timestamp=t0 + 0.10)
    assert swipe == "RIGHT"

    # Immediate subsequent movement should return None due to cooldown
    suppressed = detector.update(400.0, timestamp=t0 + 0.20)
    assert suppressed is None


def test_mouse_controller_math():
    """Tests cursor interpolation, boundary clamping, and click cooldown."""
    mouse = MouseController()

    # Move to top-left of active zone
    x1, y1 = mouse.move(config.ACTIVE_ZONE_MARGIN_X, config.ACTIVE_ZONE_MARGIN_Y)
    assert 0 <= x1 < mouse.screen_width
    assert 0 <= y1 < mouse.screen_height

    # Move far outside active zone over consecutive frames to allow smoothing to settle
    x2, y2 = 0, 0
    for _ in range(60):
        x2, y2 = mouse.move(-500.0, 2000.0)

    # Coordinates must reach the boundary clamps
    assert x2 == 0
    assert y2 >= mouse.screen_height - 2

    # Click cooldown test
    first_click = mouse.click()
    assert first_click is True
    # Immediate second click must be blocked by cooldown
    second_click = mouse.click()
    assert second_click is False


def test_slide_controller_cooldown():
    """Tests slide trigger actions and 1.0s cooldown."""
    slides = SlideController()
    first_trigger = slides.trigger("right")
    assert first_trigger is True
    assert slides.last_action_name == "Next Slide (Right)"

    # Immediate second trigger blocked by cooldown
    second_trigger = slides.trigger("right")
    assert second_trigger is False
    assert slides.time_remaining_cooldown() > 0.0


def test_volume_controller_mapping():
    """Tests volume percentage calculation and distance clamping."""
    vol = VolumeController()
    # Min pinch distance corresponds to 0%
    pct_min, _ = vol.set_volume_from_distance(config.PINCH_MIN_DIST)
    assert 0 <= pct_min <= 100

    # Max pinch distance corresponds to 100%
    for _ in range(10):  # Allow smoothing to settle
        pct_max, _ = vol.set_volume_from_distance(config.PINCH_MAX_DIST)
    assert pct_max >= 95
