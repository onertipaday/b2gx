from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

CHUNK = 1 << 20

# Cloudflare (purl.obolibrary.org, current.geneontology.org) returns HTTP 403 for
# the default "Python-urllib/x.y" User-Agent, so send an explicit one.
USER_AGENT = "b2gx/0.1 (+https://github.com/onertipaday/b2gx)"

# Default source URLs (used by the CLI `fetch` command on an internet node).
SOURCES = {
    "go_basic": "https://purl.obolibrary.org/obo/go/go-basic.obo",
    "interpro2go": "https://ftp.ebi.ac.uk/pub/databases/GO/goa/external2go/interpro2go",
    "ec2go": "https://current.geneontology.org/ontology/external2go/ec2go",
    "idmapping": "https://ftp.uniprot.org/pub/databases/uniprot/current_release/"
                 "knowledgebase/idmapping/idmapping_selected.tab.gz",
    "gene2accession": "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2accession.gz",
    "gene2go": "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz",
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
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(req) as r, dest.open("wb") as out:  # noqa: S310
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


def build_reference_cache(cache_dir: str | Path) -> None:
    """Download all reference sources and build the merged acc2go.parquet index.

    Combines two independent (acc, go_id) sources: UniProt idmapping (keyed on
    both RefSeq and EMBL-CDS/GenBank accessions) and NCBI gene2accession/gene2go
    (keyed on RefSeq protein accessions NCBI itself maps to GO but UniProt
    doesn't carry). The two intermediate Parquets are kept in cache_dir for
    inspection rather than written to a temp dir.
    """
    from b2gx.refdata.lookups import (
        build_accession_index, build_gene2go_index, merge_acc2go_indexes,
    )

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    entries: dict[str, dict] = {}
    for key, url in SOURCES.items():
        dest = cache_dir / Path(url).name
        logger.info("Downloading %s <- %s", key, url)
        download(url, dest)
        entries[key] = {"path": str(dest), "url": url}
    write_manifest(cache_dir / "manifest.json", entries)

    uniprot_idx = cache_dir / "acc2go_uniprot.parquet"
    gene2go_idx = cache_dir / "acc2go_gene2go.parquet"
    final_idx = cache_dir / "acc2go.parquet"

    logger.info("Building UniProt-derived index (RefSeq + EMBL-CDS)")
    build_accession_index(entries["idmapping"]["path"], uniprot_idx)

    logger.info("Building NCBI gene2go-derived index")
    build_gene2go_index(
        entries["gene2accession"]["path"], entries["gene2go"]["path"], gene2go_idx
    )

    logger.info("Merging accession indexes into %s", final_idx)
    merge_acc2go_indexes([uniprot_idx, gene2go_idx], final_idx)
