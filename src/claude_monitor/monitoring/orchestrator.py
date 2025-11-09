"""Orchestrator for monitoring components."""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from claude_monitor.core.plans import DEFAULT_TOKEN_LIMIT, get_token_limit
from claude_monitor.error_handling import report_error
from claude_monitor.monitoring.data_manager import DataManager
from claude_monitor.monitoring.session_monitor import SessionMonitor
from claude_monitor.utils.time_utils import TimezoneHandler, format_display_time

logger = logging.getLogger(__name__)


class MonitoringOrchestrator:
    """Orchestrates monitoring components following SRP."""

    def __init__(
        self, update_interval: int = 10, data_path: Optional[str] = None
    ) -> None:
        """Initialize orchestrator with components.

        Args:
            update_interval: Seconds between updates
            data_path: Optional path to Claude data directory
        """
        self.update_interval: int = update_interval

        self.data_manager: DataManager = DataManager(cache_ttl=5, data_path=data_path)
        self.session_monitor: SessionMonitor = SessionMonitor()

        self._monitoring: bool = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._update_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._last_valid_data: Optional[Dict[str, Any]] = None
        self._args: Optional[Any] = None
        self._first_data_event: threading.Event = threading.Event()

    def start(self) -> None:
        """Start monitoring."""
        if self._monitoring:
            logger.warning("Monitoring already running")
            return

        logger.info(f"Starting monitoring with {self.update_interval}s interval")
        self._monitoring = True
        self._stop_event.clear()

        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop, name="MonitoringThread", daemon=True
        )
        self._monitor_thread.start()

    def stop(self) -> None:
        """Stop monitoring."""
        if not self._monitoring:
            return

        logger.info("Stopping monitoring")
        self._monitoring = False
        self._stop_event.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

        self._monitor_thread = None
        self._first_data_event.clear()

    def set_args(self, args: Any) -> None:
        """Set command line arguments for token limit calculation.

        Args:
            args: Command line arguments
        """
        self._args = args

    def register_update_callback(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register callback for data updates.

        Args:
            callback: Function to call with monitoring data
        """
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)
            logger.debug("Registered update callback")

    def register_session_callback(
        self, callback: Callable[[str, str, Optional[Dict[str, Any]]], None]
    ) -> None:
        """Register callback for session changes.

        Args:
            callback: Function(event_type, session_id, session_data)
        """
        self.session_monitor.register_callback(callback)

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """Get the current monitoring data.

        Returns:
            Current monitoring data or None if not available
        """
        return self._last_valid_data

    def force_refresh(self) -> Optional[Dict[str, Any]]:
        """Force immediate data refresh.

        Returns:
            Fresh data or None if fetch fails
        """
        return self._fetch_and_process_data(force_refresh=True)

    def wait_for_initial_data(self, timeout: float = 10.0) -> bool:
        """Wait for initial data to be fetched.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if data was received, False if timeout
        """
        return self._first_data_event.wait(timeout=timeout)

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Monitoring loop started")

        # Initial fetch
        self._fetch_and_process_data()

        while self._monitoring:
            # Wait for interval or stop
            if self._stop_event.wait(timeout=self.update_interval):
                if not self._monitoring:
                    break

            # Fetch and process
            self._fetch_and_process_data()

        logger.info("Monitoring loop ended")

    def _fetch_and_process_data(
        self, force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Fetch data and notify callbacks.

        Args:
            force_refresh: Force cache refresh

        Returns:
            Processed data or None if failed
        """
        try:
            # Fetch data
            start_time: float = time.time()
            data: Optional[Dict[str, Any]] = self.data_manager.get_data(
                force_refresh=force_refresh
            )

            if data is None:
                logger.warning("No data fetched")
                return None

            # Validate and update session tracking
            is_valid: bool
            errors: List[str]
            is_valid, errors = self.session_monitor.update(data)
            if not is_valid:
                logger.error(f"Data validation failed: {errors}")
                return None

            # Calculate token limit
            token_limit: int = self._calculate_token_limit(data)

            # Extract time information from active block
            time_info = self._extract_time_info(data, token_limit)

            # Prepare monitoring data
            monitoring_data: Dict[str, Any] = {
                "data": data,
                "token_limit": token_limit,
                "args": self._args,
                "session_id": self.session_monitor.current_session_id,
                "session_count": self.session_monitor.session_count,
                **time_info,  # Include time information
            }

            # Store last valid data
            self._last_valid_data = monitoring_data

            # Signal that first data has been received
            if not self._first_data_event.is_set():
                self._first_data_event.set()

            # Notify callbacks
            for callback in self._update_callbacks:
                try:
                    callback(monitoring_data)
                except Exception as e:
                    logger.error(f"Callback error: {e}", exc_info=True)
                    report_error(
                        exception=e,
                        component="orchestrator",
                        context_name="callback_error",
                    )

            elapsed: float = time.time() - start_time
            logger.debug(f"Data processing completed in {elapsed:.3f}s")

            return monitoring_data

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
            report_error(
                exception=e, component="orchestrator", context_name="monitoring_cycle"
            )
            return None

    def _calculate_token_limit(self, data: Dict[str, Any]) -> int:
        """Calculate token limit based on plan and data.

        Args:
            data: Monitoring data

        Returns:
            Token limit
        """
        if not self._args:
            return DEFAULT_TOKEN_LIMIT

        plan: str = getattr(self._args, "plan", "pro")

        try:
            if plan == "custom":
                blocks: List[Any] = data.get("blocks", [])
                return get_token_limit(plan, blocks)
            return get_token_limit(plan)
        except Exception as e:
            logger.exception(f"Error calculating token limit: {e}")
            return DEFAULT_TOKEN_LIMIT

    def _extract_time_info(self, data: Dict[str, Any], token_limit: int) -> Dict[str, Any]:
        """Extract time information from active block.

        Args:
            data: Monitoring data
            token_limit: Current token limit

        Returns:
            Dictionary with time information and usage stats
        """
        time_info = {
            "start_time_str": "N/A",
            "reset_time_str": "N/A",
            "predicted_end_str": "N/A",
            "tokens_used": 0,
            "reset_time_utc": None,  # datetime object for comparison
            "predicted_end_utc": None,  # datetime object for comparison
        }

        try:
            # Find active block
            active_block = None
            for block in data.get("blocks", []):
                if isinstance(block, dict) and block.get("isActive", False):
                    active_block = block
                    break

            if not active_block:
                return time_info

            # Get timezone from args
            tz_handler = TimezoneHandler(default_tz="Europe/Warsaw")
            timezone_str = getattr(self._args, "timezone", "Europe/Warsaw") if self._args else "Europe/Warsaw"

            if not tz_handler.validate_timezone(timezone_str):
                timezone_str = "Europe/Warsaw"

            # Get time format preference
            time_format = "12h" if self._args and getattr(self._args, "time_12h", False) else "24h"

            # Extract tokens used
            tokens_used = active_block.get("totalTokens", 0)
            time_info["tokens_used"] = tokens_used

            # Extract and format start time
            start_time_str = active_block.get("startTime")
            if start_time_str:
                try:
                    start_time = tz_handler.parse_timestamp(start_time_str)
                    start_time_utc = tz_handler.ensure_utc(start_time)
                    start_time_local = tz_handler.convert_to_timezone(start_time_utc, timezone_str)
                    time_info["start_time_str"] = format_display_time(
                        start_time_local, time_format, include_seconds=False
                    )
                except Exception as e:
                    logger.debug(f"Error formatting start time: {e}")

            # Extract and format reset time (endTime)
            reset_time_str = active_block.get("endTime")
            if reset_time_str:
                try:
                    reset_time = tz_handler.parse_timestamp(reset_time_str)
                    reset_time_utc = tz_handler.ensure_utc(reset_time)
                    reset_time_local = tz_handler.convert_to_timezone(reset_time_utc, timezone_str)
                    time_info["reset_time_str"] = format_display_time(
                        reset_time_local, time_format, include_seconds=False
                    )
                    time_info["reset_time_utc"] = reset_time_utc  # Store UTC datetime for comparison
                except Exception as e:
                    logger.debug(f"Error formatting reset time: {e}")

            # Calculate predicted end time based on burn rate
            print(f"[ORCH DEBUG] Calculating predicted end - token_limit: {token_limit}, tokens_used: {tokens_used}")
            if token_limit > 0 and tokens_used > 0:
                try:
                    # Get duration in minutes
                    duration_minutes = active_block.get("durationMinutes", 0)
                    print(f"[ORCH DEBUG] duration_minutes: {duration_minutes}")

                    if duration_minutes > 0:
                        # Calculate burn rate (tokens per minute)
                        burn_rate = tokens_used / duration_minutes

                        # Calculate remaining tokens
                        remaining_tokens = token_limit - tokens_used

                        if remaining_tokens > 0 and burn_rate > 0:
                            # Calculate minutes until tokens run out
                            minutes_remaining = remaining_tokens / burn_rate

                            # Calculate predicted end time
                            current_time = datetime.now(timezone.utc)
                            from datetime import timedelta
                            predicted_end_time = current_time + timedelta(minutes=minutes_remaining)

                            # Store UTC datetime for comparison
                            time_info["predicted_end_utc"] = predicted_end_time

                            # Format predicted end time
                            predicted_end_local = tz_handler.convert_to_timezone(predicted_end_time, timezone_str)
                            time_info["predicted_end_str"] = format_display_time(
                                predicted_end_local, time_format, include_seconds=False
                            )
                            print(f"[ORCH DEBUG] Predicted end time calculated: {time_info['predicted_end_str']}")
                        elif remaining_tokens <= 0:
                            # Already exceeded the limit
                            time_info["predicted_end_str"] = "Exceeded"
                            print(f"[ORCH DEBUG] Tokens exceeded")
                        else:
                            time_info["predicted_end_str"] = "N/A"
                            print(f"[ORCH DEBUG] Burn rate is 0, predicted end = N/A")
                    else:
                        time_info["predicted_end_str"] = "N/A"
                        print(f"[ORCH DEBUG] Duration minutes is 0, predicted end = N/A")
                except Exception as e:
                    logger.debug(f"Error calculating predicted end time: {e}")
                    time_info["predicted_end_str"] = "N/A"

        except Exception as e:
            logger.error(f"Error extracting time info: {e}", exc_info=True)

        return time_info
