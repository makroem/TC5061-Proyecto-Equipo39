"""Contrato HTTP de descarga sin depender de la disponibilidad de MiBici."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from mibici_equipo39 import dataset


@pytest.fixture
def source(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        payload = b"id,name\n1,Estacion\n"
        requests_seen = []
        failures = 0

        def do_GET(self):
            self.requests_seen.append(dict(self.headers))
            if self.headers.get("User-Agent", "").startswith("python-requests"):
                self.send_error(406)
                return
            if type(self).failures:
                type(self).failures -= 1
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(self.payload)))
            self.end_headers()
            self.wfile.write(self.payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(dataset.time, "sleep", lambda _: None)
    try:
        yield f"http://127.0.0.1:{server.server_port}/data.csv", Handler
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_download_identifies_client_and_reuses_verified_cache(source, tmp_path):
    url, handler = source
    path = tmp_path / "nested/data.csv"
    expected = hashlib.sha256(handler.payload).hexdigest()
    dataset.download_file(url, path, expected)
    assert path.read_bytes() == handler.payload
    assert handler.requests_seen[0]["User-Agent"] == dataset.DOWNLOAD_HEADERS["User-Agent"]
    dataset.download_file(url, path, expected)
    assert len(handler.requests_seen) == 1
    path.write_bytes(b"modified")
    with pytest.raises(ValueError, match="Hash distinto"):
        dataset.download_file(url, path, expected)
    assert path.read_bytes() == b"modified"
    assert len(handler.requests_seen) == 1


def test_download_retries_transient_failure(source, tmp_path):
    url, handler = source
    handler.failures = 1
    path = tmp_path / "data.csv"
    dataset.download_file(url, path)
    assert path.read_bytes() == handler.payload
    assert len(handler.requests_seen) == 2


@pytest.mark.parametrize("payload", [b"", b"<!DOCTYPE html><html>error</html>", b"id,name\n2,Changed\n"])
def test_download_rejects_invalid_content_and_cleans_partial(source, tmp_path, payload):
    url, handler = source
    expected = hashlib.sha256(handler.payload).hexdigest()
    handler.payload = payload
    path = tmp_path / "data.csv"
    with pytest.raises(RuntimeError, match="No se pudo descargar"):
        dataset.download_file(url, path, expected)
    assert not path.exists()
    assert not path.with_suffix(".csv.part").exists()
    assert len(handler.requests_seen) == 3
