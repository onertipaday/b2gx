import json
from b2gx.refdata.fetch import sha256_file, write_manifest, verify_manifest


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
