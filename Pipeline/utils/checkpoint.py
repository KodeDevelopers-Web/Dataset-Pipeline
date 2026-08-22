"""
Crash-safe checkpoint utilities for dataset pipeline resume support.
"""

from __future__ import annotations

import atexit
import json
import os
import signal
import socket
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from tempfile import mkstemp
from threading import RLock
from typing import Any, Callable, Dict, Iterator, Optional

from config import CACHE_DIR
from utils.logger import info, warning

CHECKPOINT_VERSION = 3
CHECKPOINT_INTERVAL = 1000
CHECKPOINT_TIME_INTERVAL = 30.0
CHECKPOINT_DIR = CACHE_DIR / "checkpoints"

_SHUTDOWN_EXCEPTIONS = (KeyboardInterrupt, GeneratorExit, SystemExit)


class CheckpointManager:
    """
    Owns checkpoint persistence, resume state, and shutdown handling.

    Checkpoints are written atomically by writing and fsyncing a temporary
    JSON file before replacing the live checkpoint path.
    """

    def __init__(
        self,
        checkpoint_dir: Path | None = None,
        sample_interval: int = CHECKPOINT_INTERVAL,
        time_interval: float = CHECKPOINT_TIME_INTERVAL,
    ):
        self.checkpoint_dir = checkpoint_dir or CHECKPOINT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.sample_interval = sample_interval
        self.time_interval = time_interval

        self._lock = RLock()
        self._active_dataset: str | None = None
        self._active_processed = 0
        self._active_completed = False
        self._active_started_monotonic = 0.0
        self._active_initial_processed = 0
        self._last_saved_processed = 0
        self._last_save_monotonic = 0.0
        self._before_save_hooks: list[Callable[[], Dict[str, Any] | None]] = []
        self._previous_signal_handlers: dict[int, Any] = {}
        self._hooks_installed = False
        self._install_shutdown_hooks()

    def _path(self, dataset_name: str) -> Path:
        return self.checkpoint_dir / f"{dataset_name}.json"

    def _install_shutdown_hooks(self) -> None:
        if self._hooks_installed:
            return

        atexit.register(self.force_save_active, "shutdown")

        for signal_name in ("SIGINT", "SIGTERM"):
            signum = getattr(signal, signal_name, None)
            if signum is None:
                continue
            try:
                self._previous_signal_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, self._handle_signal)
            except (OSError, RuntimeError, ValueError):
                continue

        self._hooks_installed = True

    def _handle_signal(self, signum: int, frame: Any) -> None:
        self.force_save_active("shutdown")

        previous = self._previous_signal_handlers.get(signum)
        if callable(previous):
            previous(signum, frame)

        if signum == getattr(signal, "SIGINT", None):
            raise KeyboardInterrupt
        raise SystemExit(128 + signum)

    def load(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        path = self._path(dataset_name)
        if not path.exists():
            return None

        try:
            with path.open("r", encoding="utf8") as handle:
                data = json.load(handle)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            warning(f"Ignoring corrupted checkpoint for {dataset_name}: {exc}")
            return None

        if not isinstance(data, dict):
            warning(f"Ignoring invalid checkpoint for {dataset_name}")
            return None

        if data.get("version") != CHECKPOINT_VERSION:
            warning(
                f"Ignoring incompatible checkpoint for {dataset_name}: "
                f"version {data.get('version')!r}"
            )
            return None

        return data

    def load_resume_position(self, dataset_name: str) -> int:
        checkpoint = self.load(dataset_name)
        if not checkpoint:
            return 0

        processed = int(checkpoint.get("processed", 0) or 0)
        if checkpoint.get("completed", False):
            return processed

        if processed > 0:
            info(f"Resuming dataset {dataset_name} from sample {processed:,}")
        return processed

    def has_incomplete_resume(self) -> bool:
        for path in self.checkpoint_dir.glob("*.json"):
            checkpoint = self.load(path.stem)
            if not checkpoint:
                continue
            if checkpoint.get("completed", False):
                continue
            if int(checkpoint.get("processed", 0) or 0) > 0:
                return True
        return False

    def start_dataset(self, dataset_name: str, processed: int = 0) -> None:
        now = time.monotonic()
        with self._lock:
            self._active_dataset = dataset_name
            self._active_processed = processed
            self._active_completed = False
            self._active_started_monotonic = now
            self._active_initial_processed = processed
            self._last_saved_processed = processed
            self._last_save_monotonic = now

    def update_position(self, dataset_name: str, processed: int) -> None:
        with self._lock:
            if self._active_dataset == dataset_name:
                self._active_processed = processed

    def add_before_save_hook(
        self,
        hook: Callable[[], Dict[str, Any] | None],
    ) -> Callable[[], None]:
        with self._lock:
            self._before_save_hooks.append(hook)

        def remove_hook() -> None:
            with self._lock:
                if hook in self._before_save_hooks:
                    self._before_save_hooks.remove(hook)

        return remove_hook

    @contextmanager
    def track(self, dataset_name: str, processed: int = 0) -> Iterator[None]:
        self.start_dataset(dataset_name, processed)
        try:
            yield
        except _SHUTDOWN_EXCEPTIONS:
            self.force_save_active("shutdown")
            raise
        except BaseException:
            self.force_save_active("exception")
            raise
        finally:
            with self._lock:
                if self._active_dataset == dataset_name:
                    self._active_dataset = None
                    self._active_completed = False

    def maybe_save(
        self,
        dataset_name: str,
        processed: int,
        reason: str = "periodic",
    ) -> bool:
        now = time.monotonic()
        with self._lock:
            samples_since_save = processed - self._last_saved_processed
            seconds_since_save = now - self._last_save_monotonic

        if processed <= self._last_saved_processed:
            return False

        if (
            samples_since_save >= self.sample_interval
            or seconds_since_save >= self.time_interval
        ):
            self.force_save(dataset_name, processed, reason=reason)
            return True

        return False

    def force_save_active(self, reason: str = "shutdown") -> None:
        with self._lock:
            dataset_name = self._active_dataset
            processed = self._active_processed
            completed = self._active_completed

        if dataset_name is None or completed:
            return

        self.force_save(
            dataset_name,
            processed,
            completed=False,
            reason=reason,
        )

    def force_save(
        self,
        dataset_name: str,
        processed: int,
        completed: bool = False,
        reason: str = "manual",
    ) -> None:
        now_monotonic = time.monotonic()
        elapsed = 0.0
        speed = 0.0
        with self._lock:
            if self._active_dataset == dataset_name:
                elapsed = max(now_monotonic - self._active_started_monotonic, 0.0)
                processed_this_run = max(
                    processed - self._active_initial_processed,
                    0,
                )
                if elapsed > 0:
                    speed = processed_this_run / elapsed

        payload = {
            "version": CHECKPOINT_VERSION,
            "dataset": dataset_name,
            "processed": processed,
            "completed": completed,
            "updated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "elapsed_seconds": round(elapsed, 3),
            "processing_speed_samples_per_sec": round(speed, 3),
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
        }

        payload["artifacts"] = self._run_before_save_hooks()
        self._atomic_write_json(self._path(dataset_name), payload)

        with self._lock:
            if self._active_dataset == dataset_name:
                self._active_processed = processed
                self._active_completed = completed
                self._last_saved_processed = processed
                self._last_save_monotonic = now_monotonic

        info(
            "Saving checkpoint:\n"
            f"Dataset: {dataset_name}\n"
            f"Processed: {processed:,}\n"
            f"Reason: {reason}"
        )

    def _run_before_save_hooks(self) -> Dict[str, Any]:
        with self._lock:
            hooks = tuple(self._before_save_hooks)

        metadata: Dict[str, Any] = {}
        for hook in hooks:
            hook_metadata = hook()
            if hook_metadata:
                metadata.update(hook_metadata)
        return metadata

    def _atomic_write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = mkstemp(
            prefix=f"{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            text=True,
        )
        temp_path = Path(temp_name)

        try:
            with os.fdopen(fd, "w", encoding="utf8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temp_path, path)
            self._fsync_directory(path.parent)
        except Exception:
            try:
                temp_path.unlink(missing_ok=True)
            finally:
                raise

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        if os.name != "posix":
            return

        directory_fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def save(
        self,
        dataset_name: str,
        processed: int,
        completed: bool = False,
    ) -> None:
        self.force_save(
            dataset_name,
            processed,
            completed=completed,
            reason="manual",
        )

    def mark_completed(
        self,
        dataset_name: str,
        processed: int | None = None,
    ) -> None:
        checkpoint = self.load(dataset_name) or {}
        if processed is None:
            processed = int(checkpoint.get("processed", 0) or 0)
        self.force_save(
            dataset_name,
            processed,
            completed=True,
            reason="completed",
        )
        info("Dataset completed.")

    def should_skip(self, dataset_name: str) -> bool:
        checkpoint = self.load(dataset_name)
        if not checkpoint:
            return False
        return bool(checkpoint.get("completed", False))

    def clear(self, dataset_name: str) -> None:
        self._path(dataset_name).unlink(missing_ok=True)

    def clear_all(self) -> None:
        for path in self.checkpoint_dir.glob("*.json"):
            path.unlink(missing_ok=True)


checkpoint_manager = CheckpointManager()
