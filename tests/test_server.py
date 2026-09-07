import io
import json

from structurelab import server


def test_failed_job_remains_pollable(tmp_path, monkeypatch):
    connection = tmp_path / "connection.json"
    connection.write_text(json.dumps({"url": "http://127.0.0.1:12345/rpc", "token": "test"}))
    monkeypatch.setattr(server, "connection_path", connection)
    failed = {"revision": "test-revision", "state": "failed", "error": "Invalid block", "captures": []}
    monkeypatch.setattr(server.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(json.dumps(failed).encode()))
    assert server.job_status("test-revision") == failed
