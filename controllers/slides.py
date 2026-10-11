"""Presentation slide controller using keyboard arrow keys with cooldown."""

import time
from typing import Optional
import pyautogui

import config


class SlideController:
    """Handles next and previous slide actions with cooldown to prevent duplicate triggers."""

    def __init__(self) -> None:
        self.last_action_time: float = 0.0
        self.last_action_name: Optional[str] = None

    def trigger(self, direction: str) -> bool:
        """Triggers a slide advance or slide back.

        Args:
            direction: Either 'next'/'right' or 'prev'/'left'.

        Returns:
            True if action was executed, False if inside cooldown.
        """
        now = time.time()
        if now - self.last_action_time < config.SLIDE_COOLDOWN:
            return False

        direction_clean = direction.strip().lower()
        if direction_clean in ("next", "right"):
            pyautogui.press("right")
            self.last_action_time = now
            self.last_action_name = "Next Slide (Right)"
            return True
        elif direction_clean in ("prev", "previous", "left"):
            pyautogui.press("left")
            self.last_action_time = now
            self.last_action_name = "Prev Slide (Left)"
            return True

        return False

    def next_slide(self) -> bool:
        """Advances to next slide."""
        return self.trigger("next")

    def prev_slide(self) -> bool:
        """Moves to previous slide."""
        return self.trigger("prev")

    def time_remaining_cooldown(self) -> float:
        """Returns seconds remaining in cooldown, or 0.0 if ready."""
        elapsed = time.time() - self.last_action_time
        remaining = config.SLIDE_COOLDOWN - elapsed
        return max(0.0, remaining)
