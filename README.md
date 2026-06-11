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

## Known limitations (follow-up work)

- **KEGG KO/pathway is not yet wired into `run`.** The pipeline supports KEGG
  (`assign_kegg`), but the CLI does not yet build the `acc2ko` / `ko2path` maps
  from the UniProt idmapping KEGG column, so `kegg_ko` / `kegg_pathways` are
  currently empty on a real run and `kegg_term2gene.tsv` is header-only. EC (via
  `ec2go`) and GO are fully wired. This was the deferred "fragile point" in the
  design (spec §5).
- **`interpro2go` is fetched but unused.** GO terms come from the InterProScan
  TSV's own GO column; the standalone `interpro2go` IPR→GO map is reserved for a
  future "map raw IPR domains without a full InterProScan run" path.
- **Per-stage checkpoint subcommands (`map`/`annotate`/…) are not implemented.**
  `run` is a single pass; resuming a preempted SLURM job re-runs from the start.
  The pipeline is composable, so adding thin checkpoint subcommands is mechanical.
