"""Publish machine playback state for sidecar services.

The controller owns the USB serial port, so a timelapse recorder cannot ask
the machine whether a job is running. This module writes a small JSON file
the recorder can poll.

``CARVERA_JOB_STATE`` selects the path. When unset, the file is
``~/.carvera/job-state.json``. An empty value disables publishing.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

_HEARTBEAT_SEC = 5.0
_last_key: tuple | None = None
_last_written = 0.0


def state_path() -> str:
    """Return the configured job-state path. Empty means publishing is off."""
    configured = os.environ.get("CARVERA_JOB_STATE")
    if configured is None:
        return os.path.join(os.path.expanduser("~"), ".carvera", "job-state.json")
    return configured


def publish(*, state: str, playing: bool, file: str, remote_path: str, local_path: str) -> None:
    """Write the job-state file if the snapshot changed, or on a short heartbeat."""
    global _last_key, _last_written

    path = state_path()
    if not path:
        return

    key = (state, bool(playing), file, remote_path, local_path)
    now = time.time()
    if key == _last_key and now - _last_written < _HEARTBEAT_SEC:
        return

    payload = {
        "state": state,
        "playing": bool(playing),
        "file": file,
        "remote_path": remote_path,
        "local_path": local_path,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    os.replace(temporary, path)
    _last_key = key
    _last_written = now
