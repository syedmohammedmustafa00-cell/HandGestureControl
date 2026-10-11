"""Main application entry point for Hand Gesture Control.

Controls computer mouse, volume, and presentation slides using webcam gestures.
"""

import sys
import time
from typing import Optional, Tuple
import cv2
import numpy as np

import config
from controllers import MouseController, SlideController, VolumeController
from gestures import (
    SwipeDetector,
    calculate_distance,
    classify_gesture,
    count_fingers_up,
)
from hand_tracker import HandTracker


class GestureControlApp:
    """Orchestrates video capture, gesture detection, and hardware controllers."""

    def __init__(self) -> None:
        self.mouse_ctrl = MouseController()
        self.vol_ctrl = VolumeController()
        self.slide_ctrl = SlideController()
        self.swipe_detector = SwipeDetector()

        self.current_mode: str = "PAUSE"
        self.candidate_mode: str = "PAUSE"
        self.mode_candidate_count: int = 0

        # Performance monitoring
        self.prev_frame_time: float = 0.0
        self.fps: float = 0.0

        # Visual feedback states
        self.status_message: str = "Ready"
        self.status_message_time: float = 0.0

    def set_status(self, message: str) -> None:
        """Sets a temporary status notification displayed on the video feed."""
        self.status_message = message
        self.status_message_time = time.time()

    def update_mode_with_debounce(self, detected_gesture: str) -> None:
        """Applies debounce logic so mode changes require consecutive consistent frames."""
        if detected_gesture == self.candidate_mode:
            self.mode_candidate_count += 1
            if self.mode_candidate_count >= config.MODE_DEBOUNCE_FRAMES:
                if self.current_mode != self.candidate_mode:
                    self.current_mode = self.candidate_mode
                    self.set_status(f"Mode switched to {self.current_mode}")
        else:
            self.candidate_mode = detected_gesture
            self.mode_candidate_count = 1

    def draw_hud(
        self,
        frame: cv2.Mat,
        has_hand: bool,
        vol_pct: int,
        is_clicking: bool,
    ) -> None:
        """Draws professional on-screen heads-up display (HUD)."""
        # 1. Top HUD Bar (Dark semi-transparent header)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (config.FRAME_WIDTH, 60), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # 2. FPS Counter
        fps_text = f"FPS: {int(self.fps)}"
        cv2.putText(
            frame,
            fps_text,
            (15, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # 3. Active Mode Display
        if not has_hand:
            mode_display = "NO HAND"
            mode_color = config.COLOR_NO_HAND
        else:
            mode_display = f"MODE: {self.current_mode}"
            if self.current_mode == "MOUSE":
                mode_color = config.COLOR_MOUSE_MODE
            elif self.current_mode == "VOLUME":
                mode_color = config.COLOR_VOLUME_MODE
            elif self.current_mode == "SLIDE":
                mode_color = config.COLOR_SLIDE_MODE
            elif self.current_mode == "PAUSE":
                mode_color = config.COLOR_PAUSE_MODE
            else:
                mode_color = config.COLOR_TEXT

        cv2.putText(
            frame,
            mode_display,
            (150, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            mode_color,
            2,
            cv2.LINE_AA,
        )

        # 4. Mode-specific overlays
        if self.current_mode == "MOUSE" and has_hand:
            # Draw Active Zone bounding box
            x_min = config.ACTIVE_ZONE_MARGIN_X
            y_min = config.ACTIVE_ZONE_MARGIN_Y
            x_max = config.FRAME_WIDTH - config.ACTIVE_ZONE_MARGIN_X
            y_max = config.FRAME_HEIGHT - config.ACTIVE_ZONE_MARGIN_Y

            cv2.rectangle(
                frame,
                (x_min, y_min),
                (x_max, y_max),
                config.COLOR_ACTIVE_ZONE,
                2,
            )
            cv2.putText(
                frame,
                "Active Zone",
                (x_min + 5, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                config.COLOR_ACTIVE_ZONE,
                1,
                cv2.LINE_AA,
            )

            if is_clicking:
                cv2.putText(
                    frame,
                    "* CLICK *",
                    (config.FRAME_WIDTH - 150, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

        elif self.current_mode == "VOLUME" and has_hand:
            # Draw vertical Volume Bar on the left side
            bar_x1, bar_y1 = 25, 120
            bar_x2, bar_y2 = 55, 380
            bar_height = bar_y2 - bar_y1
            fill_height = int(bar_height * (vol_pct / 100.0))

            # Background bar
            cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (50, 50, 50), -1)
            # Filled bar
            cv2.rectangle(
                frame,
                (bar_x1, bar_y2 - fill_height),
                (bar_x2, bar_y2),
                config.COLOR_VOLUME_MODE,
                -1,
            )
            # Outline
            cv2.rectangle(
                frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (255, 255, 255), 2
            )
            # Percentage text
            cv2.putText(
                frame,
                f"{vol_pct}%",
                (bar_x1 - 5, bar_y2 + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                config.COLOR_TEXT,
                2,
                cv2.LINE_AA,
            )

        elif self.current_mode == "SLIDE" and has_hand:
            cooldown_left = self.slide_ctrl.time_remaining_cooldown()
            cd_status = (
                "READY" if cooldown_left == 0.0 else f"WAIT {cooldown_left:.1f}s"
            )
            cd_color = (0, 255, 0) if cooldown_left == 0.0 else (0, 165, 255)
            cv2.putText(
                frame,
                f"Slide: {cd_status}",
                (config.FRAME_WIDTH - 220, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                cd_color,
                2,
                cv2.LINE_AA,
            )

        # 5. Bottom Notification / Instruction Banner
        now = time.time()
        if (now - self.status_message_time) < 2.0:
            msg_to_show = self.status_message
        else:
            if self.current_mode == "MOUSE":
                msg_to_show = "Index: Move cursor | Index+Middle close: Click"
            elif self.current_mode == "VOLUME":
                msg_to_show = "Pinch thumb & index: Adjust volume"
            elif self.current_mode == "SLIDE":
                msg_to_show = "Fast swipe OR two fingers: Previous/Next slide"
            elif self.current_mode == "PAUSE":
                msg_to_show = "Fist detected: Paused. Raise index finger to resume."
            else:
                msg_to_show = "Press ESC to exit"

        cv2.putText(
            frame,
            msg_to_show,
            (15, config.FRAME_HEIGHT - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

    def run(self) -> None:
        """Main application loop."""
        print("=" * 60)
        print("  Starting Hand Gesture Control System (Windows)")
        print(f"  Camera Index: {config.CAMERA_INDEX}")
        print("  Press 'ESC' in the video window to quit safely.")
        print("=" * 60)

        # Try DirectShow first on Windows for faster webcam initialization, fallback to default backend
        cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not cap.isOpened():
            print(
                f"[ERROR] Could not open camera at index {config.CAMERA_INDEX}.\n"
                "Please verify that your webcam is connected and not in use by another app."
            )
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        tracker = HandTracker()

        window_name = "Hand Gesture Control - (Press ESC to exit)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

        self.prev_frame_time = time.time()

        try:
            while True:
                success, frame = cap.read()
                if not success or frame is None:
                    print("[Warning] Failed to grab frame. Retrying...")
                    time.sleep(0.05)
                    continue

                # 1. Flip frame horizontally for natural mirror behavior
                frame = cv2.flip(frame, 1)

                # 2. Track hand and extract landmarks
                frame = tracker.find_hands(frame, draw=True)
                landmarks, hand_label = tracker.find_positions(frame)

                has_hand = len(landmarks) >= 21
                is_clicking = False
                vol_pct = self.vol_ctrl.get_current_percentage()

                if has_hand:
                    fingers = count_fingers_up(landmarks, hand_label=hand_label)
                    detected_gesture = classify_gesture(fingers, landmarks)

                    # Update mode with debounce filter
                    self.update_mode_with_debounce(detected_gesture)

                    # Execute actions based on current active mode
                    if self.current_mode == "MOUSE":
                        # Index tip is landmark 8
                        index_tip_x, index_tip_y = landmarks[8][1], landmarks[8][2]
                        self.mouse_ctrl.move(index_tip_x, index_tip_y)

                        # Check for click condition (index 8 and middle 12 close together)
                        middle_tip_x, middle_tip_y = (
                            landmarks[12][1],
                            landmarks[12][2],
                        )
                        tip_dist = calculate_distance(
                            (index_tip_x, index_tip_y),
                            (middle_tip_x, middle_tip_y),
                        )

                        # Highlight fingertips and connecting segment
                        cv2.line(
                            frame,
                            (index_tip_x, index_tip_y),
                            (middle_tip_x, middle_tip_y),
                            (255, 0, 255),
                            2,
                        )

                        if tip_dist < config.CLICK_DISTANCE_THRESHOLD:
                            clicked = self.mouse_ctrl.click()
                            if clicked:
                                is_clicking = True
                                self.set_status("Left Click!")
                                cv2.circle(
                                    frame,
                                    (
                                        (index_tip_x + middle_tip_x) // 2,
                                        (index_tip_y + middle_tip_y) // 2,
                                    ),
                                    12,
                                    (0, 255, 0),
                                    -1,
                                )

                    elif self.current_mode == "VOLUME":
                        # Thumb tip is 4, Index tip is 8
                        thumb_x, thumb_y = landmarks[4][1], landmarks[4][2]
                        index_x, index_y = landmarks[8][1], landmarks[8][2]
                        pinch_dist = calculate_distance(
                            (thumb_x, thumb_y), (index_x, index_y)
                        )

                        vol_pct, _ = self.vol_ctrl.set_volume_from_distance(pinch_dist)

                        # Draw line and center circle representing pinch
                        cx, cy = (thumb_x + index_x) // 2, (thumb_y + index_y) // 2
                        cv2.line(
                            frame, (thumb_x, thumb_y), (index_x, index_y), (255, 200, 0), 2
                        )
                        cv2.circle(frame, (cx, cy), 8, config.COLOR_VOLUME_MODE, -1)

                    elif self.current_mode == "SLIDE":
                        # Check horizontal swipe from wrist (0) or index MCP (5)
                        wrist_x = landmarks[0][1]
                        swipe = self.swipe_detector.update(wrist_x)

                        if swipe == "RIGHT":
                            if self.slide_ctrl.next_slide():
                                self.set_status("Next Slide ->")
                        elif swipe == "LEFT":
                            if self.slide_ctrl.prev_slide():
                                self.set_status("<- Previous Slide")
                        else:
                            # Also support static two-finger gesture trigger:
                            # If index & middle up and spread apart, advance slide
                            index_tip_x = landmarks[8][1]
                            wrist_x = landmarks[0][1]
                            # If hand tilted towards right edge, trigger next; tilted left, trigger prev
                            if index_tip_x > (wrist_x + 50):
                                if self.slide_ctrl.next_slide():
                                    self.set_status("Next Slide (Two Fingers ->)")
                            elif index_tip_x < (wrist_x - 50):
                                if self.slide_ctrl.prev_slide():
                                    self.set_status("<- Prev Slide (Two Fingers)")

                    elif self.current_mode == "PAUSE":
                        # Closed fist: do nothing
                        pass

                else:
                    # Hand not in view
                    pass

                # Calculate live FPS
                curr_time = time.time()
                time_delta = curr_time - self.prev_frame_time
                if time_delta > 0:
                    self.fps = 1.0 / time_delta
                self.prev_frame_time = curr_time

                # Draw Heads Up Display
                self.draw_hud(frame, has_hand, vol_pct, is_clicking)

                # Show frame in OpenCV window
                cv2.imshow(window_name, frame)

                # Press ESC (ASCII 27) to cleanly exit
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    print("\n[INFO] ESC key pressed. Shutting down gracefully...")
                    break

        except KeyboardInterrupt:
            print("\n[INFO] KeyboardInterrupt received. Shutting down...")
        finally:
            cap.release()
            tracker.close()
            cv2.destroyAllWindows()
            print("[INFO] Camera released and windows closed safely.")


def main() -> None:
    """Entry point function."""
    app = GestureControlApp()
    app.run()


if __name__ == "__main__":
    main()
