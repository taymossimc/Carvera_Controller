"""Job-state file written for sidecar services."""

import json
import os

from carveracontroller import jobstate


def test_publish_writes_playback_snapshot(tmp_path, monkeypatch):
    destination = tmp_path / "job-state.json"
    monkeypatch.setenv("CARVERA_JOB_STATE", str(destination))
    jobstate._last_key = None
    jobstate._last_written = 0.0

    jobstate.publish(
        state="Run",
        playing=True,
        file="bracket.nc",
        remote_path="/sd/bracket.nc",
        local_path="/jobs/bracket.nc",
    )

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["state"] == "Run"
    assert payload["playing"] is True
    assert payload["file"] == "bracket.nc"
    assert payload["remote_path"] == "/sd/bracket.nc"
    assert payload["local_path"] == "/jobs/bracket.nc"
    assert payload["updated"].endswith("Z")


def test_empty_path_disables_publishing(tmp_path, monkeypatch):
    monkeypatch.setenv("CARVERA_JOB_STATE", "")
    jobstate._last_key = None
    jobstate._last_written = 0.0
    jobstate.publish(state="Idle", playing=False, file="", remote_path="", local_path="")
    assert list(tmp_path.iterdir()) == []


def test_jobs_directory_uses_existing_env_path(tmp_path, monkeypatch):
    from carveracontroller.Utils import jobs_directory

    missing = tmp_path / "absent"
    monkeypatch.setenv("CARVERA_JOBS_DIR", str(missing))
    assert jobs_directory() == ""

    monkeypatch.setenv("CARVERA_JOBS_DIR", str(tmp_path))
    assert jobs_directory() == os.path.abspath(tmp_path)
