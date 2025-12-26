import os
import platform
import subprocess
from enum import Enum


class AlertType(Enum):
    """Types of audio alerts."""

    ORDER_CREATED = "order_created"
    ORDER_FILLED = "order_filled"
    TP_HIT = "tp_hit"
    GRID_ACTIVATED = "grid_activated"
    GRID_PAUSED = "grid_paused"
    GRID_INACTIVE = "grid_inactive"
    CYCLE_ACTIVATED = "cycle_activated"
    CYCLE_DEACTIVATED = "cycle_deactivated"
    ERROR = "error"


class AudioAlerts:
    """Audio alert system for the trading bot."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.system = platform.system()

    def _play_beep(self, count: int = 1, duration_ms: int = 100) -> None:
        """Play system beep sound."""
        if not self.enabled:
            return

        try:
            if self.system == "Darwin":  # macOS
                for _ in range(count):
                    os.system("afplay /System/Library/Sounds/Glass.aiff &")
            elif self.system == "Linux":
                for _ in range(count):
                    subprocess.run(
                        ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                        capture_output=True,
                    )
            elif self.system == "Windows":
                import winsound

                for _ in range(count):
                    winsound.Beep(1000, duration_ms)  # type: ignore[attr-defined]
            else:
                # Fallback: print bell character
                print("\a" * count, end="", flush=True)
        except Exception:
            # Silently fail if audio doesn't work
            print("\a" * count, end="", flush=True)

    def play(self, alert_type: AlertType) -> None:
        """Play alert based on type."""
        if not self.enabled:
            return

        alert_config = {
            AlertType.ORDER_CREATED: (1, 100),  # 1 beep, 100ms
            AlertType.ORDER_FILLED: (1, 150),  # 1 beep, 150ms
            AlertType.TP_HIT: (2, 150),  # 2 beeps
            AlertType.GRID_ACTIVATED: (1, 300),  # 1 long beep
            AlertType.GRID_PAUSED: (2, 100),  # 2 short beeps
            AlertType.GRID_INACTIVE: (3, 100),  # 3 short beeps
            AlertType.CYCLE_ACTIVATED: (2, 200),  # 2 medium beeps
            AlertType.CYCLE_DEACTIVATED: (1, 200),  # 1 medium beep
            AlertType.ERROR: (4, 200),  # 4 beeps
        }

        count, duration = alert_config.get(alert_type, (1, 100))
        self._play_beep(count, duration)

    def order_filled(self) -> None:
        """Alert for filled order."""
        self.play(AlertType.ORDER_FILLED)

    def tp_hit(self) -> None:
        """Alert for take profit hit."""
        self.play(AlertType.TP_HIT)

    def grid_activated(self) -> None:
        """Alert for grid activation."""
        self.play(AlertType.GRID_ACTIVATED)

    def grid_paused(self) -> None:
        """Alert for grid pause."""
        self.play(AlertType.GRID_PAUSED)

    def grid_inactive(self) -> None:
        """Alert for grid inactive."""
        self.play(AlertType.GRID_INACTIVE)

    def error(self) -> None:
        """Alert for error."""
        self.play(AlertType.ERROR)

    def cycle_activated(self) -> None:
        """Alert for manual cycle activation."""
        self.play(AlertType.CYCLE_ACTIVATED)

    def cycle_deactivated(self) -> None:
        """Alert for manual cycle deactivation."""
        self.play(AlertType.CYCLE_DEACTIVATED)

    def toggle(self) -> bool:
        """Toggle alerts on/off."""
        self.enabled = not self.enabled
        return self.enabled
