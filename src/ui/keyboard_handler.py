"""
Keyboard handler for dashboard controls.

Reads from stdin - only captures when terminal is focused.
"""

import select
import sys
import termios
import threading
import time
import tty
from collections.abc import Callable
from enum import Enum

from src.utils.logger import main_logger


class KeyAction(Enum):
    """Available keyboard actions."""

    ACTIVATE_CYCLE = "activate"
    DEACTIVATE_CYCLE = "deactivate"
    QUIT = "quit"
    RESTART_GRID = "restart"


class KeyboardHandler:
    """
    Handles keyboard input from stdin.

    Only captures when terminal is in focus.

    Supported keys:
    - A: Activate cycle manually
    - D: Deactivate cycle
    - Q: Quit application
    - R: Restart grid
    """

    DEBOUNCE_TIME = 0.5  # 500ms debounce

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._running = False
        self._callbacks: dict[KeyAction, Callable] = {}
        self._lock = threading.Lock()
        self._last_key_time: dict[str, float] = {}
        self._old_settings = None

    def set_callback(self, action: KeyAction, callback: Callable) -> None:
        """Set callback for a specific action."""
        with self._lock:
            self._callbacks[action] = callback

    def start(self) -> None:
        """Start the keyboard listener in a separate thread."""
        if self._running:
            return

        self._running = True

        # Save terminal settings and set to raw mode
        try:
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except Exception:
            # Not a TTY, skip keyboard handling
            main_logger.warning("Não é um terminal TTY - controles de teclado desativados")
            self._running = False
            return

        self._thread = threading.Thread(target=self._input_loop, daemon=True)
        self._thread.start()
        main_logger.info("Keyboard handler iniciado (stdin)")

    def stop(self) -> None:
        """Stop the keyboard listener."""
        self._running = False

        # Restore terminal settings
        if self._old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
            except Exception:
                pass

        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

        main_logger.info("Keyboard handler encerrado")

    def _input_loop(self) -> None:
        """Main input loop - reads from stdin."""
        while self._running:
            try:
                # Check if input is available (with timeout)
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1).lower()
                    self._handle_key(char)
            except Exception:
                # Terminal closed or error
                break

    def _handle_key(self, char: str) -> None:
        """Handle a key press."""
        # Check debounce
        current_time = time.time()
        last_time = self._last_key_time.get(char, 0)
        if current_time - last_time < self.DEBOUNCE_TIME:
            return
        self._last_key_time[char] = current_time

        action = None
        if char == "a":
            action = KeyAction.ACTIVATE_CYCLE
        elif char == "d":
            action = KeyAction.DEACTIVATE_CYCLE
        elif char == "q":
            action = KeyAction.QUIT
        elif char == "r":
            action = KeyAction.RESTART_GRID

        if action:
            self._execute_callback(action)

    def _execute_callback(self, action: KeyAction) -> None:
        """Execute the callback for an action."""
        with self._lock:
            callback = self._callbacks.get(action)

        if callback:
            try:
                callback()
            except Exception as e:
                main_logger.error(f"Erro no callback {action.value}: {e}")
