"""Filesystem lock helpers for planloop sessions."""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

LOCK_FILE = ".lock"
LOCK_INFO_FILE = ".lock_info"
DEFAULT_TIMEOUT = 30
SLEEP_INTERVAL = 0.1


@dataclass
class LockInfo:
    held_by: str
    since: float
    operation: str

    def to_dict(self) -> dict:
        return {"held_by": self.held_by, "since": self.since, "operation": self.operation}

    @classmethod
    def from_file(cls, path: Path) -> "LockInfo | None":
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        except json.JSONDecodeError:
            return None


@dataclass
class LockStatus:
    locked: bool
    info: Optional[LockInfo]


@contextmanager
def acquire_lock(session_dir: Path, operation: str, timeout: int = DEFAULT_TIMEOUT) -> Iterator[None]:
    lock_path = session_dir / LOCK_FILE
    info_path = session_dir / LOCK_INFO_FILE
    start = time.time()
    held_by = f"pid:{os.getpid()}"

    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            info = LockInfo(held_by=held_by, since=time.time(), operation=operation)
            info_path.write_text(json.dumps(info.to_dict()), encoding="utf-8")
            break
        except FileExistsError:
            if timeout == 0:
                raise TimeoutError("Lock already held")
            if time.time() - start > timeout:
                info = LockInfo.from_file(info_path)
                holder = info.held_by if info else "unknown"
                raise TimeoutError(f"Lock held by {holder} longer than {timeout}s")
            time.sleep(SLEEP_INTERVAL)

    try:
        yield
    finally:
        if lock_path.exists():
            lock_path.unlink()
        if info_path.exists():
            info_path.unlink()


def get_lock_status(session_dir: Path) -> LockStatus:
    lock_path = session_dir / LOCK_FILE
    info_path = session_dir / LOCK_INFO_FILE
    locked = lock_path.exists()
    info = LockInfo.from_file(info_path) if locked else None
    return LockStatus(locked=locked, info=info)
