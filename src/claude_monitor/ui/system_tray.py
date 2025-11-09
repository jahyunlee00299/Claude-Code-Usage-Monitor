"""System tray manager for Windows taskbar integration."""

import logging
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SystemTrayManager:
    """Manages system tray icon and notifications.

    This class handles:
    - System tray icon creation and management
    - Context menu with actions
    - Real-time tooltip updates
    - Windows notifications
    - Integration with MonitoringOrchestrator

    Attributes:
        orchestrator: The monitoring orchestrator instance
        icon: The pystray icon instance
        current_status: Current status message
        _stop_event: Threading event for clean shutdown
    """

    def __init__(self, orchestrator):
        """Initialize system tray manager.

        Args:
            orchestrator: MonitoringOrchestrator instance
        """
        try:
            import pystray
        except ImportError:
            logger.error(
                "pystray is not installed. Install with: pip install 'claude-monitor[tray]'"
            )
            raise ImportError(
                "pystray is required for system tray. "
                "Install with: pip install 'claude-monitor[tray]'"
            )

        self.orchestrator = orchestrator
        self.icon: Optional["pystray.Icon"] = None
        self.current_status = "Waiting..."
        self._stop_event = threading.Event()
        self._last_notification_time = 0
        self._notification_cooldown = 300  # 5 minutes between notifications
        self.is_monitoring = False  # Track monitoring status

        # Double-click detection
        self._last_click_time = 0
        self._click_timer = None
        self._double_click_threshold = 0.5  # 500ms for double-click detection

    def create_menu(self):
        """Create system tray context menu.

        Returns:
            pystray.Menu: Context menu for tray icon
        """
        try:
            import pystray
            from pystray import MenuItem as item
        except ImportError:
            raise ImportError(
                "pystray is required. Install with: pip install 'claude-monitor[tray]'"
            )

        return pystray.Menu(
            # Hidden default action for left-click/double-click
            item("Open Monitor", self.on_double_click, default=True, visible=False),
            item("Show Status", self.show_status),
            item("Settings", self.open_settings),
            pystray.Menu.SEPARATOR,
            item(
                "Monitoring",
                pystray.Menu(
                    item("Start", self.start_monitoring, enabled=lambda _: not self.is_monitoring),
                    item("Stop", self.stop_monitoring, enabled=lambda _: self.is_monitoring),
                ),
            ),
            pystray.Menu.SEPARATOR,
            item("Exit", self.quit_app),
        )

    def show_status(self, icon=None, item=None):
        """Display current status as notification.

        Args:
            icon: pystray icon instance (unused, required by pystray)
            item: menu item instance (unused, required by pystray)
        """
        try:
            # Get latest monitoring data
            monitoring_data = self.orchestrator.get_current_data()

            if not monitoring_data:
                message = "No data available"
            else:
                data = monitoring_data.get("data", {})

                if data and "blocks" in data:
                    blocks = data.get("blocks", [])
                    active_blocks = [b for b in blocks if b.get("isActive")]

                    if active_blocks:
                        block = active_blocks[0]
                        tokens = block.get("totalTokens", 0)
                        cost = block.get("totalCost", 0.0)
                        messages = block.get("messageCount", 0)

                        # Get token limit
                        token_limit = monitoring_data.get("token_limit", 0)

                        # Get time information
                        start_time = monitoring_data.get("start_time_str", "N/A")
                        reset_time = monitoring_data.get("reset_time_str", "N/A")
                        predicted_end = monitoring_data.get("predicted_end_str", "N/A")

                        message = (
                            f"Tokens: {tokens:,} / {token_limit:,}\n"
                            f"Cost: ${cost:.2f}\n"
                            f"Messages: {messages}\n"
                            f"─────────────────\n"
                            f"세션 시작: {start_time}\n"
                            f"리셋: {reset_time}\n"
                            f"소진 예정: {predicted_end}"
                        )
                    else:
                        message = "No active session"
                else:
                    message = "No data available"

            # Show Windows notification
            if self.icon:
                self.icon.notify(message, "Claude Usage Monitor")

        except Exception as e:
            logger.error(f"Error showing status: {e}", exc_info=True)
            if self.icon:
                self.icon.notify("Error occurred", "Claude Monitor")

    def open_settings(self, icon=None, item=None):
        """Open settings window (placeholder).

        Args:
            icon: pystray icon instance (unused)
            item: menu item instance (unused)
        """
        if self.icon:
            self.icon.notify(
                "Settings feature coming soon!\nUse CLI arguments for now.",
                "Claude Monitor"
            )

    def start_monitoring(self, icon=None, item=None):
        """Start monitoring.

        Args:
            icon: pystray icon instance (unused)
            item: menu item instance (unused)
        """
        if not self.is_monitoring:
            try:
                self.orchestrator.start()
                self.is_monitoring = True
            except Exception as e:
                logger.debug(f"Start monitoring: {e}")
            if self.icon:
                self.icon.notify("Monitoring started", "Claude Monitor")
            logger.info("Monitoring started via tray menu")

    def stop_monitoring(self, icon=None, item=None):
        """Stop monitoring.

        Args:
            icon: pystray icon instance (unused)
            item: menu item instance (unused)
        """
        if self.is_monitoring:
            try:
                self.orchestrator.stop()
                self.is_monitoring = False
            except Exception as e:
                logger.debug(f"Stop monitoring: {e}")
            if self.icon:
                self.icon.notify("Monitoring stopped", "Claude Monitor")
            logger.info("Monitoring stopped via tray menu")

    def quit_app(self, icon=None, item=None):
        """Quit application.

        Args:
            icon: pystray icon instance (unused)
            item: menu item instance (unused)
        """
        logger.info("User requested exit via tray menu")
        self.orchestrator.stop()
        self._stop_event.set()
        if self.icon:
            self.icon.stop()

    def on_double_click(self, icon=None, item=None):
        """Handle clicks on tray icon with double-click detection.

        Only launches monitor on actual double-click (two clicks within 500ms).
        Single clicks are ignored.

        Args:
            icon: pystray icon instance (unused)
            item: menu item instance (unused)
        """
        import time

        current_time = time.time()
        time_since_last_click = current_time - self._last_click_time

        logger.debug(f"Click detected. Time since last click: {time_since_last_click:.3f}s")

        # Check if this is a double-click (within threshold)
        if time_since_last_click < self._double_click_threshold:
            # This is a double-click!
            logger.info("=== DOUBLE-CLICK DETECTED - Launching monitor in CMD ===")

            # Cancel any pending single-click timer
            if self._click_timer:
                self._click_timer.cancel()
                self._click_timer = None

            # Reset click time to prevent triple-click triggering another launch
            self._last_click_time = 0

            # Launch the monitor
            self._launch_monitor()
        else:
            # This is a single click - wait to see if another click follows
            logger.debug("Single click detected, waiting for potential double-click...")

            # Cancel any previous timer
            if self._click_timer:
                self._click_timer.cancel()

            # Update last click time
            self._last_click_time = current_time

            # Set timer to reset click state after threshold
            # (This prevents treating two widely-spaced single clicks as a double-click)
            self._click_timer = threading.Timer(
                self._double_click_threshold,
                self._reset_click_state
            )
            self._click_timer.start()

    def _reset_click_state(self):
        """Reset click state after double-click threshold expires."""
        logger.debug("Click state reset - single click ignored")
        self._last_click_time = 0
        self._click_timer = None

    def _launch_monitor(self):
        """Launch claude-monitor in a new CMD window."""
        try:
            # Launch claude-monitor in a new CMD window
            # /k keeps the window open after command execution
            if sys.platform == "win32":
                cmd = ['cmd', '/k', 'python', '-m', 'claude_monitor']
                logger.info(f"Executing command: {' '.join(cmd)}")

                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                logger.info(f"Monitor launched in new CMD window (PID: {process.pid})")
            else:
                # For non-Windows platforms, use default terminal
                subprocess.Popen(['python', '-m', 'claude_monitor'])
                logger.info("Monitor launched in default terminal")

            # Show confirmation notification
            if self.icon:
                self.icon.notify(
                    "Opening Claude Monitor in new window...",
                    "Claude Monitor"
                )

        except Exception as e:
            logger.error(f"Error launching monitor in CMD: {e}", exc_info=True)
            if self.icon:
                self.icon.notify(
                    f"Failed to launch monitor: {e}",
                    "Claude Monitor Error"
                )

    def update_tooltip(self, monitoring_data: Dict[str, Any]):
        """Update tooltip with current usage data.

        Args:
            monitoring_data: Current monitoring data from orchestrator
        """
        try:
            # monitoring_data에서 직접 정보 가져오기
            tokens_used = monitoring_data.get("tokens_used", 0)
            token_limit = monitoring_data.get("token_limit", 0)

            # 남은 토큰 및 퍼센트 계산
            remaining_tokens = max(0, token_limit - tokens_used) if token_limit > 0 else 0
            remaining_pct = (remaining_tokens / token_limit * 100) if token_limit > 0 else 100

            # 시간 정보 가져오기 (이미 포맷팅된 문자열)
            start_time_str = monitoring_data.get("start_time_str", "")
            reset_time_str = monitoring_data.get("reset_time_str", "")
            predicted_end_str = monitoring_data.get("predicted_end_str", "")

            # 세션 시작 시간
            session_start = start_time_str if start_time_str else "N/A"

            # 리셋 시간
            reset_time = reset_time_str if reset_time_str else "N/A"

            # 토큰 소진 예상 시간
            tokens_runout = predicted_end_str if predicted_end_str else "N/A"

            tooltip = (
                f"세션 시작: {session_start} | "
                f"리셋: {reset_time} | "
                f"토큰 소진: {tokens_runout} | "
                f"남은 예산: {remaining_pct:.0f}%"
            )

            if self.icon:
                self.icon.title = tooltip

            # Get cost from data if available
            cost = 0.0
            data = monitoring_data.get("data", {})
            if data and "blocks" in data:
                blocks = data.get("blocks", [])
                active_blocks = [b for b in blocks if b.get("isActive")]
                if active_blocks:
                    cost = active_blocks[0].get("totalCost", 0.0)

            # Check for high usage and send warning
            self._check_usage_threshold(tokens_used, token_limit, cost)

        except Exception as e:
            logger.error(f"Error updating tooltip: {e}", exc_info=True)
            if self.icon:
                self.icon.title = "Error updating status"

    def _check_usage_threshold(self, tokens: int, token_limit: int, cost: float):
        """Check if usage exceeds threshold and send notification.

        Args:
            tokens: Current token usage
            token_limit: Token limit
            cost: Current cost
        """
        import time

        if token_limit <= 0:
            return

        usage_pct = (tokens / token_limit) * 100

        # Only notify if cooldown has passed
        current_time = time.time()
        if current_time - self._last_notification_time < self._notification_cooldown:
            return

        # Send warning at 80% and 90% usage
        if usage_pct >= 90:
            if self.icon:
                self.icon.notify(
                    f"⚠️ Token usage: {usage_pct:.1f}%\n"
                    f"Tokens: {tokens:,}/{token_limit:,}\n"
                    f"Cost: ${cost:.2f}\n"
                    f"Approaching limit!",
                    "⚠️ Claude Monitor Warning",
                )
                self._last_notification_time = current_time
                logger.warning(f"High usage warning sent: {usage_pct:.1f}%")

        elif usage_pct >= 80:
            if self.icon:
                self.icon.notify(
                    f"Token usage: {usage_pct:.1f}%\n"
                    f"Tokens: {tokens:,}/{token_limit:,}\n"
                    f"Cost: ${cost:.2f}",
                    "Claude Monitor",
                )
                self._last_notification_time = current_time
                logger.info(f"Usage notification sent: {usage_pct:.1f}%")

    def run(self):
        """Run system tray in blocking mode.

        This method:
        1. Creates the tray icon
        2. Registers callbacks
        3. Starts monitoring
        4. Runs the icon (blocking)
        """
        try:
            import pystray

            from claude_monitor.ui.tray_icon import create_icon_image
        except ImportError as e:
            logger.error(f"Import error: {e}")
            raise ImportError(
                "Required packages not installed. "
                "Install with: pip install 'claude-monitor[tray]'"
            )

        try:
            # Create icon image
            image = create_icon_image()

            # Create tray icon with double-click handler (via menu default item)
            self.icon = pystray.Icon(
                "claude_monitor",
                image,
                "Claude Code Usage Monitor",
                self.create_menu()
            )

            # Register monitoring callbacks
            self.orchestrator.register_update_callback(self.update_tooltip)

            # Start monitoring
            try:
                self.orchestrator.start()
            except Exception as e:
                logger.debug(f"Orchestrator start: {e}")

            logger.info("System tray mode started")

            # Show startup notification
            self.icon.notify(
                "Claude Monitor is now running in the system tray.\n"
                "Right-click the icon for options.",
                "Claude Monitor Started"
            )

            # Run icon (blocking call)
            self.icon.run()

        except Exception as e:
            logger.error(f"Error running system tray: {e}", exc_info=True)
            raise

        finally:
            # Cleanup
            self.orchestrator.stop()
            logger.info("System tray stopped")

    def stop(self):
        """Stop the tray manager."""
        if self.icon:
            self.icon.stop()
        self.orchestrator.stop()
        self._stop_event.set()


def check_tray_support() -> bool:
    """Check if system tray is supported on this platform.

    Returns:
        bool: True if tray is supported, False otherwise
    """
    try:
        import pystray

        return True
    except ImportError:
        logger.warning(
            "pystray not installed. Install with: pip install 'claude-monitor[tray]'"
        )
        return False
