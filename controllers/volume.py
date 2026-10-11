"""System volume controller for Windows using pycaw."""

from typing import Optional, Tuple
import numpy as np

import config

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False


class VolumeController:
    """Manages Windows system master volume based on hand pinch gestures."""

    def __init__(self) -> None:
        self.endpoint_volume: Optional[object] = None
        self.current_volume_pct: float = 50.0

        if PYCAW_AVAILABLE:
            try:
                speakers = AudioUtilities.GetSpeakers()
                # Modern pycaw provides EndpointVolume directly on AudioDevice
                if hasattr(speakers, "EndpointVolume") and speakers.EndpointVolume is not None:
                    self.endpoint_volume = speakers.EndpointVolume
                elif hasattr(speakers, "Activate"):
                    interface = speakers.Activate(
                        IAudioEndpointVolume._iid_,
                        CLSCTX_ALL,
                        None,
                    )
                    self.endpoint_volume = cast(interface, POINTER(IAudioEndpointVolume))
                elif hasattr(speakers, "_dev") and hasattr(speakers._dev, "Activate"):
                    interface = speakers._dev.Activate(
                        IAudioEndpointVolume._iid_,
                        CLSCTX_ALL,
                        None,
                    )
                    self.endpoint_volume = cast(interface, POINTER(IAudioEndpointVolume))

                if self.endpoint_volume is not None:
                    # Retrieve current system volume scalar (0.0 to 1.0)
                    current_scalar = self.endpoint_volume.GetMasterVolumeLevelScalar()
                    self.current_volume_pct = float(current_scalar * 100.0)
            except Exception as exc:
                print(f"[Warning] Could not initialize Windows audio endpoint: {exc}")
                self.endpoint_volume = None

    def set_volume_from_distance(self, distance: float) -> Tuple[int, int]:
        """Maps pinch distance to volume percentage and applies smoothing.

        Args:
            distance: Euclidean distance between thumb tip and index tip in pixels.

        Returns:
            Tuple of (volume_percentage [0-100], volume_bar_level [pixels or 0-100]).
        """
        target_pct = float(
            np.interp(
                distance,
                [config.PINCH_MIN_DIST, config.PINCH_MAX_DIST],
                [0.0, 100.0],
            )
        )
        target_pct = float(np.clip(target_pct, 0.0, 100.0))

        # Smooth changes to avoid sudden jumps
        smoothening = max(1.0, config.VOLUME_SMOOTHENING)
        self.current_volume_pct += (target_pct - self.current_volume_pct) / smoothening
        clamped_pct = int(np.clip(round(self.current_volume_pct), 0, 100))

        if self.endpoint_volume is not None:
            try:
                scalar = clamped_pct / 100.0
                self.endpoint_volume.SetMasterVolumeLevelScalar(scalar, None)
            except Exception as exc:
                # Catch temporary COM errors safely
                pass

        return clamped_pct, clamped_pct

    def get_current_percentage(self) -> int:
        """Returns the current smoothed volume percentage."""
        return int(round(self.current_volume_pct))
