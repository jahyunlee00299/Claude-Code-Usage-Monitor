"""System tray manager for Windows taskbar integration."""

import logging
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
            item("Show Status", self.show_status),
            item("Settings", self.open_settings),
            pystray.Menu.SEPARATOR,
            item(
                "Monitoring",
                pystray.Menu(
                    item("Start", self.start_monitoring, enabled=lambda _: not self.orchestrator.is_running()),
                    item("Stop", self.stop_monitoring, enabled=lambda _: self.orchestrator.is_running()),
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
            data = self.orchestrator.get_current_data()

            if data and "blocks" in data:
                blocks = data.get("blocks", [])
                active_blocks = [b for b in blocks if b.get("isActive")]

                if active_blocks:
                    block = active_blocks[0]
                    tokens = block.get("totalTokens", 0)
                    cost = block.get("totalCost", 0.0)
                    messages = block.get("messageCount", 0)

                    message = (
                        f"Tokens: {tokens:,}\n"
                        f"Cost: ${cost:.2f}\n"
                        f"Messages: {messages}"
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
        if not self.orchestrator.is_running():
            self.orchestrator.start()
            if self.icon:
                self.icon.notify("Monitoring started", "Claude Monitor")
            logger.info("Monitoring started via tray menu")

    def stop_monitoring(self, icon=None, item=None):
        """Stop monitoring.

        Args:
            icon: pystray icon instance (unused)
            item: menu item instance (unused)
        """
        if self.orchestrator.is_running():
            self.orchestrator.stop()
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

    def update_tooltip(self, monitoring_data: Dict[str, Any]):
        """Update tooltip with current usage data.

        Args:
            monitoring_data: Current monitoring data from orchestrator
        """
        try:
            data = monitoring_data.get("data", {})
            blocks = data.get("blocks", [])
            active_blocks = [b for b in blocks if b.get("isActive")]

            if active_blocks and self.icon:
                block = active_blocks[0]
                tokens = block.get("totalTokens", 0)
                cost = block.get("totalCost", 0.0)
                token_limit = monitoring_data.get("token_limit", 0)

                # Calculate usage percentage
                usage_pct = 0
                if token_limit > 0:
                    usage_pct = (tokens / token_limit) * 100

                tooltip = (
                    f"Claude Monitor | "
                    f"Tokens: {tokens:,} | "
                    f"${cost:.2f} | "
                    f"{usage_pct:.0f}%"
                )

                self.icon.title = tooltip

                # Check for high usage and send warning
                self._check_usage_threshold(tokens, token_limit, cost)

            elif self.icon:
                self.icon.title = "Claude Monitor | No active session"

        except Exception as e:
            logger.error(f"Error updating tooltip: {e}", exc_info=True)

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

            # Create tray icon
            self.icon = pystray.Icon(
                "claude_monitor", image, "Claude Code Usage Monitor", self.create_menu()
            )

            # Register monitoring callbacks
            self.orchestrator.register_update_callback(self.update_tooltip)

            # Start monitoring
            if not self.orchestrator.is_running():
                self.orchestrator.start()

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
