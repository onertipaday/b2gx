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

## Known limitations

- **GO coverage is bounded by UniProt idmapping, which is thin for prokaryotes.**
  In the Chroococcidiopsis `GCF_023558375.1` acceptance run (5,627 proteins,
  DIAMOND vs nr), only **~10%** of DIAMOND subject accessions resolved to GO and
  3,207/5,627 sequences were annotated. This is a source-coverage ceiling, not a
  bug: subject accessions and the index keys are both versioned and match (a
  resolvable WP_ maps correctly), but of 70,144 unique RefSeq subjects only 12,509
  (17.8%) are present in `idmapping_selected.tab.gz`, and the ~53k GenBank-type
  subjects (e.g. `AAT41948.1`) are not keyed at all. The `mapping` stage emits a
  coverage report so this is always visible. **Roadmap (TODO):** add the design's
  noted RefSeq-native supplement — NCBI `gene2accession → gene2go` — to map RefSeq
  protein accessions to GO directly; this lifts coverage substantially for
  bacteria/archaea. A cheaper partial step is to also key the index on the UniProt
  EMBL-CDS column so GenBank-type subjects resolve via UniProt.
- **KEGG KO/pathway is intentionally descoped — not a TODO.** The original design
  assumed UniProt `idmapping_selected.tab.gz` carried KEGG/KO columns; it does
  **not** (its 22 columns have no KEGG, KO, or EC field — col 18 is EMBL-CDS).
  `idmapping.dat.gz` exposes only KEGG *gene* IDs, and going gene→KO→pathway
  requires the KEGG REST API, which is excluded for licensing. So KO/pathway
  cannot be transferred license-free by homology and `b2gx` does not emit them:
  `kegg_ko` / `kegg_pathways` stay empty and `kegg_term2gene.tsv` is header-only.
  GO and EC (via `ec2go`) are fully wired. To add KO for downstream
  clusterProfiler KEGG enrichment, run **KofamScan** (KOfam HMMs, license-clean)
  separately and join its KO calls on `seq_id`. The `assign_kegg` plumbing is
  retained dormant so such a KO source can be wired in without code changes.
- **`interpro2go` is fetched but unused.** GO terms come from the InterProScan
  TSV's own GO column; the standalone `interpro2go` IPR→GO map is reserved for a
  future "map raw IPR domains without a full InterProScan run" path.
- **Per-stage checkpoint subcommands (`map`/`annotate`/…) are not implemented.**
  `run` is a single pass; resuming a preempted SLURM job re-runs from the start.
  The pipeline is composable, so adding thin checkpoint subcommands is mechanical.
