from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.request

CHUNK = 1 << 20

# Default source URLs (used by the CLI `fetch` command on an internet node).
SOURCES = {
    "go_basic": "https://purl.obolibrary.org/obo/go/go-basic.obo",
    "interpro2go": "https://ftp.ebi.ac.uk/pub/databases/GO/goa/external2go/interpro2go",
    "ec2go": "https://current.geneontology.org/ontology/external2go/ec2go",
    "idmapping": "https://ftp.uniprot.org/pub/databases/uniprot/current_release/"
                 "knowledgebase/idmapping/idmapping_selected.tab.gz",
}


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: str | Path) -> None:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, dest.open("wb") as out:  # noqa: S310
        while chunk := r.read(CHUNK):
            out.write(chunk)


def write_manifest(manifest_path: str | Path, entries: dict[str, dict]) -> None:
    out: dict[str, dict] = {}
    now = datetime.now(timezone.utc).isoformat()
    for key, meta in entries.items():
        p = Path(meta["path"])
        out[key] = {
            "path": str(p),
            "url": meta.get("url", ""),
            "sha256": sha256_file(p),
            "size": p.stat().st_size,
            "downloaded": now,
        }
    Path(manifest_path).write_text(json.dumps(out, indent=2))


def verify_manifest(manifest_path: str | Path) -> list[str]:
    """Return a list of human-readable problems; empty list means all good."""
    data = json.loads(Path(manifest_path).read_text())
    problems: list[str] = []
    for key, meta in data.items():
        p = Path(meta["path"])
        if not p.exists():
            problems.append(f"{key}: missing file {p}")
        elif sha256_file(p) != meta["sha256"]:
            problems.append(f"{key}: sha256 mismatch for {p}")
    return problems
