"""Single instance lock mechanism for preventing duplicate processes."""

import atexit
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SingleInstanceLock:
    """Ensures only one instance of the application runs at a time.

    Uses a lock file with PID to prevent multiple instances.
    """

    def __init__(self, lock_name: str = "claude_monitor_tray"):
        """Initialize the single instance lock.

        Args:
            lock_name: Name for the lock file
        """
        self.lock_name = lock_name
        self.lock_file: Optional[Path] = None
        self.locked = False

    def acquire(self) -> bool:
        """Acquire the lock.

        Returns:
            True if lock was acquired, False if another instance is running
        """
        # Get lock file path in temp directory
        if sys.platform == "win32":
            temp_dir = Path(os.environ.get("TEMP", "C:\\Temp"))
        else:
            temp_dir = Path("/tmp")

        self.lock_file = temp_dir / f"{self.lock_name}.lock"

        # Check if lock file exists
        if self.lock_file.exists():
            try:
                # Read PID from lock file
                pid_str = self.lock_file.read_text().strip()
                if pid_str:
                    pid = int(pid_str)

                    # Check if process is still running
                    if self._is_process_running(pid):
                        logger.warning(
                            f"Another instance is already running (PID: {pid})"
                        )
                        return False
                    else:
                        # Stale lock file, remove it
                        logger.info(f"Removing stale lock file (PID: {pid})")
                        self.lock_file.unlink()
            except (ValueError, IOError) as e:
                logger.warning(f"Error reading lock file: {e}, removing it")
                try:
                    self.lock_file.unlink()
                except Exception:
                    pass

        # Create lock file with current PID
        try:
            current_pid = os.getpid()
            self.lock_file.write_text(str(current_pid))
            self.locked = True

            # Register cleanup on exit
            atexit.register(self.release)

            logger.info(f"Acquired instance lock (PID: {current_pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to create lock file: {e}")
            return False

    def release(self):
        """Release the lock."""
        if self.locked and self.lock_file and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                logger.info("Released instance lock")
            except Exception as e:
                logger.warning(f"Error removing lock file: {e}")
            finally:
                self.locked = False

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        try:
            if sys.platform == "win32":
                # On Windows, use tasklist
                import subprocess
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return str(pid) in result.stdout
            else:
                # On Unix-like systems, use os.kill with signal 0
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            return False

    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError("Another instance is already running")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
