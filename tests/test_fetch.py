import gzip
import io
import json
import urllib.request
import polars as pl
from b2gx.refdata import fetch
from b2gx.refdata.fetch import (
    SOURCES, download, sha256_file, write_manifest, verify_manifest,
    build_reference_cache,
)


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


def test_sources_include_ncbi_gene2go_supplement():
    assert SOURCES["gene2accession"] == "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2accession.gz"
    assert SOURCES["gene2go"] == "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz"


def test_build_reference_cache(tmp_path, monkeypatch):
    """Stub out network downloads; verify the merged acc2go.parquet and manifest."""
    payloads = {
        "go-basic.obo": b"format-version: 1.2\n",
        "interpro2go": b"!comment\n",
        "ec2go": b"!comment\n",
    }

    idmap_row = ["P1", "ID", "1", "WP_idmap.1", "", "", "GO:0000001"] + [""] * 15
    idmap_buf = io.BytesIO()
    with gzip.GzipFile(fileobj=idmap_buf, mode="wb") as gz:
        gz.write(("\t".join(idmap_row) + "\n").encode())
    payloads["idmapping_selected.tab.gz"] = idmap_buf.getvalue()

    g2a_buf = io.BytesIO()
    with gzip.GzipFile(fileobj=g2a_buf, mode="wb") as gz:
        gz.write(b"#tax_id\tGeneID\tstatus\tRNA\tRNA_gi\tprotein_accession.version\n")
        gz.write(b"1\t100\tPROVISIONAL\t-\t-\tWP_gene2go.1\n")
    payloads["gene2accession.gz"] = g2a_buf.getvalue()

    g2g_buf = io.BytesIO()
    with gzip.GzipFile(fileobj=g2g_buf, mode="wb") as gz:
        gz.write(b"#tax_id\tGeneID\tGO_ID\tEvidence\tQualifier\tGO_term\tPubMed\tCategory\n")
        gz.write(b"1\t100\tGO:0000002\tIEA\t-\tx\t-\tProcess\n")
    payloads["gene2go.gz"] = g2g_buf.getvalue()

    def fake_download(url, dest):
        from pathlib import Path
        name = Path(url).name
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(payloads[name])

    monkeypatch.setattr(fetch, "download", fake_download)
    build_reference_cache(tmp_path)

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert set(manifest) == {
        "go_basic", "interpro2go", "ec2go", "idmapping", "gene2accession", "gene2go",
    }

    final = pl.read_parquet(tmp_path / "acc2go.parquet")
    accs_gos = set(zip(final["acc"], final["go_id"]))
    assert ("WP_idmap.1", "GO:0000001") in accs_gos  # from UniProt idmapping
    assert ("WP_gene2go.1", "GO:0000002") in accs_gos  # from NCBI gene2go join
