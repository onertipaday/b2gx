import io
import json
import urllib.request
from b2gx.refdata import fetch
from b2gx.refdata.fetch import download, sha256_file, write_manifest, verify_manifest


def test_download_sends_user_agent(tmp_path, monkeypatch):
    """Cloudflare 403s the default Python-urllib UA; download() must set one."""
    captured = {}

    def fake_urlopen(req, *args, **kwargs):
        captured["url"] = req.full_url
        captured["ua"] = req.get_header("User-agent")
        return io.BytesIO(b"payload")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    dest = tmp_path / "go-basic.obo"
    download("https://purl.obolibrary.org/obo/go/go-basic.obo", dest)

    assert captured["ua"], "no User-Agent header set on the request"
    assert "Python-urllib" not in captured["ua"]
    assert dest.read_bytes() == b"payload"


def test_manifest_roundtrip_and_verify(tmp_path):
    f = tmp_path / "go-basic.obo"
    f.write_text("format-version: 1.2\n")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, {"go_basic": {"path": str(f), "url": "http://x/go-basic.obo"}})
    data = json.loads(manifest.read_text())
    assert data["go_basic"]["sha256"] == sha256_file(f)
    assert verify_manifest(manifest) == []  # no problems


def test_verify_detects_tampering(tmp_path):
    f = tmp_path / "go-basic.obo"
    f.write_text("a\n")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, {"go_basic": {"path": str(f), "url": "u"}})
    f.write_text("tampered\n")
    problems = verify_manifest(manifest)
    assert problems and "go_basic" in problems[0]
