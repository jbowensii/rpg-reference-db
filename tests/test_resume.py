import contextlib

import httpx

import refdb.downloads as d


def test_download_resumes_after_drop(monkeypatch) -> None:
    data = bytes(range(256)) * 40
    calls = []

    class Resp:
        def __init__(self, status, body, die):
            self.status_code, self.body, self.die = status, body, die

        def raise_for_status(self):
            pass

        def iter_raw(self, size):
            yield self.body[:3000]
            if self.die:
                raise httpx.RemoteProtocolError("peer closed")
            yield self.body[3000:]

    @contextlib.contextmanager
    def fake_stream(method, url, headers=None, **kw):
        rng = (headers or {}).get("Range")
        start = int(rng.split("=")[1].rstrip("-")) if rng else 0
        calls.append(start)
        yield Resp(206 if start else 200, data[start:], die=len(calls) == 1)

    monkeypatch.setattr(d.httpx, "stream", fake_stream)
    monkeypatch.setattr(d.time, "sleep", lambda s: None)
    assert b"".join(d._resumable_bytes("https://x.test/f")) == data
    assert calls == [0, 3000]
