"""MediaPipe Hands wrapper module for hand detection and landmark extraction."""

from typing import Any, List, Optional, Tuple
import cv2
import mediapipe as mp

import config


class HandTracker:
    """Wrapper class for MediaPipe Hands detection and landmark extraction."""

    def __init__(
        self,
        max_num_hands: int = config.MP_MAX_NUM_HANDS,
        min_detection_confidence: float = config.MP_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence: float = config.MP_MIN_TRACKING_CONFIDENCE,
    ) -> None:
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles
        self.results: Optional[Any] = None

    def find_hands(self, frame: cv2.Mat, draw: bool = True) -> cv2.Mat:
        """Processes the frame to detect hands and optionally draws landmarks.

        Args:
            frame: OpenCV BGR image frame.
            draw: Whether to draw landmarks on the frame.

        Returns:
            Annotated OpenCV BGR image frame.
        """
        if frame is None or frame.size == 0:
            return frame

        # Convert BGR image to RGB for MediaPipe processing
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        self.results = self.hands.process(frame_rgb)
        frame_rgb.flags.writeable = True

        if draw and self.results and self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw_styles.get_default_hand_landmarks_style(),
                    self.mp_draw_styles.get_default_hand_connections_style(),
                )
        return frame

    def find_positions(
        self, frame: cv2.Mat, hand_no: int = 0
    ) -> Tuple[List[Tuple[int, int, int]], Optional[str]]:
        """Extracts pixel coordinates of landmarks and hand classification (Left/Right).

        Args:
            frame: OpenCV image frame used to convert normalized coords to pixels.
            hand_no: Index of detected hand (defaults to 0 for single hand).

        Returns:
            Tuple of:
              - List of (landmark_id, x_pixel, y_pixel)
              - Hand classification string ('Left' or 'Right'), or None if no hand detected.
        """
        landmark_list: List[Tuple[int, int, int]] = []
        hand_label: Optional[str] = None

        if frame is None or frame.size == 0:
            return landmark_list, hand_label

        if (
            self.results
            and self.results.multi_hand_landmarks
            and len(self.results.multi_hand_landmarks) > hand_no
        ):
            target_hand = self.results.multi_hand_landmarks[hand_no]
            h, w, _ = frame.shape

            for lm_id, lm in enumerate(target_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmark_list.append((lm_id, cx, cy))

            # Retrieve handedness (Left vs Right) if available
            if (
                self.results.multi_handedness
                and len(self.results.multi_handedness) > hand_no
            ):
                hand_label = (
                    self.results.multi_handedness[hand_no].classification[0].label
                )

        return landmark_list, hand_label

    def close(self) -> None:
        """Releases MediaPipe resources."""
        if hasattr(self, "hands") and self.hands is not None:
            self.hands.close()
