"""Mouse controller for moving the cursor and triggering left clicks."""

import time
from typing import Tuple
import numpy as np
import pyautogui

import config

# Disable FAILSAFE to prevent crash when cursor approaches screen edges,
# since coordinates are explicitly clamped within bounds.
pyautogui.FAILSAFE = False


class MouseController:
    """Handles cursor positioning, smoothing, and clicking."""

    def __init__(self) -> None:
        self.screen_width, self.screen_height = pyautogui.size()
        # Initialize smoothed coordinates at center of screen
        self.prev_x: float = self.screen_width / 2.0
        self.prev_y: float = self.screen_height / 2.0
        self.last_click_time: float = 0.0

    def move(self, tip_x: float, tip_y: float) -> Tuple[int, int]:
        """Maps active zone coordinates to screen and applies exponential smoothing.

        Args:
            tip_x: X coordinate of index fingertip in camera frame.
            tip_y: Y coordinate of index fingertip in camera frame.

        Returns:
            Tuple of current smoothed (screen_x, screen_y).
        """
        # Active zone boundaries
        x_min = config.ACTIVE_ZONE_MARGIN_X
        x_max = config.FRAME_WIDTH - config.ACTIVE_ZONE_MARGIN_X
        y_min = config.ACTIVE_ZONE_MARGIN_Y
        y_max = config.FRAME_HEIGHT - config.ACTIVE_ZONE_MARGIN_Y

        # Linear interpolation from camera active zone to monitor screen size
        target_x = np.interp(tip_x, (x_min, x_max), (0, self.screen_width - 1))
        target_y = np.interp(tip_y, (y_min, y_max), (0, self.screen_height - 1))

        # Exponential smoothing: curr = prev + (target - prev) / smoothening
        smoothening = max(1.0, config.MOUSE_SMOOTHENING)
        curr_x = self.prev_x + (target_x - self.prev_x) / smoothening
        curr_y = self.prev_y + (target_y - self.prev_y) / smoothening

        # Clamp within screen bounds
        clamped_x = int(np.clip(curr_x, 0, self.screen_width - 1))
        clamped_y = int(np.clip(curr_y, 0, self.screen_height - 1))

        # Update cursor position and internal state
        pyautogui.moveTo(clamped_x, clamped_y)
        self.prev_x = curr_x
        self.prev_y = curr_y

        return clamped_x, clamped_y

    def click(self) -> bool:
        """Triggers a left mouse click if the cooldown period has elapsed.

        Returns:
            True if a click was performed, False if within cooldown.
        """
        now = time.time()
        if now - self.last_click_time >= config.CLICK_COOLDOWN:
            pyautogui.click()
            self.last_click_time = now
            return True
        return False
