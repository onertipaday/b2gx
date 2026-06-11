# b2gx

Blast2GO-style functional annotation as a CLI/library. Consumes DIAMOND-vs-nr
hits, applies the Blast2GO Annotation Rule (mapping → DT scoring → GO-DAG
abstraction), merges InterProScan GO terms, assigns EC + KEGG KO/pathway, and
emits clusterProfiler tables, a Blast2GO `.annot`, a rich per-sequence table, and
summary/GO-slim stats.

See `docs/superpowers/specs/` for the design and `docs/superpowers/plans/` for the
implementation plan.

## Upstream DIAMOND command

The 8 columns (including the non-default `ppos` and `qcovhsp`) are required:

```bash
diamond blastp -d nr -q protein.faa -f 6 \
  qseqid sseqid pident ppos length evalue bitscore qcovhsp -o hits.tsv
```

## Local development (uv)

```bash
uv sync
uv run pytest -q
uv run b2gx version
```

## Build the apptainer image (on a node with internet)

```bash
apptainer build /mnt/nfs3/sonegop/images/apptainer/b2gx.sif apptainer/b2gx.def
```

## Fetch references (internet node)

Downloads `go-basic.obo`, `interpro2go`, `ec2go`, and UniProt
`idmapping_selected.tab.gz`, writes a versioned `manifest.json`, and builds the
accession→GO Parquet index.

```bash
apptainer exec -B /mnt/nfs3/sonegop /mnt/nfs3/sonegop/images/apptainer/b2gx.sif \
  b2gx fetch --cache-dir /mnt/nfs3/sonegop/refdata/b2gx
```

## Run

```bash
apptainer exec -B /mnt/nfs3/sonegop /mnt/nfs3/sonegop/images/apptainer/b2gx.sif \
  b2gx run --config run.yaml \
  --obo /mnt/nfs3/sonegop/refdata/b2gx/go-basic.obo \
  --index /mnt/nfs3/sonegop/refdata/b2gx/acc2go.parquet \
  --ec2go /mnt/nfs3/sonegop/refdata/b2gx/ec2go
```

Outputs (in `out_dir` from `run.yaml`): `go_term2gene.tsv`, `go_term2name.tsv`,
`kegg_term2gene.tsv`, `annotation.annot`, `annotation.parquet`, `summary.txt`.
