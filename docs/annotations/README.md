# b2gx Annotation Outputs — Enrichment Workflow

This directory holds **ready-to-use** GO annotation outputs from b2gx runs,
saved alongside the repo so they don't require HPC access to consume. Each
organism subdirectory (`pn40024/`, `chroococcidiopsis/`) contains:

| File | Format | Use |
|---|---|---|
| `annotation.annot` | `seq_id\tGO:id` (Blast2GO-compatible, 2-column) | Drop-in replacement for a Blast2GO `.annot` file in any tool that consumes one |
| `go_term2gene.tsv` | `go_id\tseq_id` | `TERM2GENE` input for `clusterProfiler::enricher()` |
| `go_term2name.tsv` | `go_id\tname` | `TERM2NAME` input for `clusterProfiler::enricher()` |
| `summary.txt` | key-value | Coverage stats for that specific run (sequences annotated, GO counts by namespace) |

Both are from the 2026-06-17 rerun against the **expanded reference index**
(UniProt idmapping keyed on RefSeq + EMBL-CDS, merged with an NCBI
gene2accession/gene2go supplement — see `docs/ACCEPTANCE.md` /
`docs/ACCEPTANCE_PN40024.md` for the full before/after numbers).

## Running a GO enrichment (clusterProfiler, R)

```r
library(clusterProfiler)

term2gene <- read.delim("docs/annotations/pn40024/go_term2gene.tsv")
term2name <- read.delim("docs/annotations/pn40024/go_term2name.tsv")

# your differentially-expressed gene list — seq_id values matching the
# protein IDs used in the annotation (e.g. Vitvi05_01chr00g00010_t001_CDS1.prot)
de_genes <- readLines("my_de_gene_list.txt")

ego <- enricher(
  gene = de_genes,
  TERM2GENE = term2gene,
  TERM2NAME = term2name,
  pvalueCutoff = 0.05,
  pAdjustMethod = "BH"
)

dotplot(ego)
```

The same `term2gene`/`term2name` pair also works with
`clusterProfiler::GSEA()` (ranked gene list) or any other tool that accepts a
generic GMT-style term↔gene mapping — see Case 3 below if you need a `.gmt`
file instead.

## Workflow: when do you need to rerun anything?

You do **not** need to rerun the b2gx pipeline for every new enrichment
analysis on an already-annotated organism — only in the cases below.

### Case 1 — Same proteome, new DE gene list (most common)
Nothing to rerun. Reuse the files in this directory directly, as in the R
snippet above.

### Case 2 — Updated proteome / new gene models for the same organism
The shared reference index (`acc2go.parquet` on HPC) doesn't need rebuilding
— only the per-organism annotation step:

```bash
# on HPC, from /mnt/nfs3/sonegop/projects/b2gx
PROJ=/mnt/nfs3/sonegop/projects/b2gx
CACHE=/mnt/nfs3/sonegop/refdata/b2gx
NR=/mnt/scratch2/sonegop/references/nr.dmnd
WORK="$PROJ/runs/<organism>"   # pick a new/unique name
mkdir -p "$WORK"

# 1. DIAMOND blastp vs nr for the new protein FASTA (8 required columns)
apptainer exec -B /mnt/nfs3/sonegop -B /mnt/scratch2/sonegop \
  /mnt/nfs3/sonegop/images/apptainer/diamond.sif \
  diamond blastp -d "$NR" -q <new_protein.faa> \
  -f 6 qseqid sseqid pident ppos length evalue bitscore qcovhsp \
  -o "$WORK/hits.tsv" -p 32 --quiet

# 2. b2gx run against the existing (already-expanded) reference cache
cat > "$WORK/run.yaml" <<YAML
query_fasta: <new_protein.faa>
diamond_tsv: $WORK/hits.tsv
cache_dir: $CACHE
out_dir: $WORK/out
annotation:
  annotation_cutoff: 55
  go_weight: 5
YAML

apptainer exec -B /mnt/nfs3/sonegop "$PROJ"/../../images/apptainer/b2gx.sif \
  b2gx run --config "$WORK/run.yaml" \
  --obo "$CACHE/go-basic.obo" --index "$CACHE/acc2go.parquet" \
  --ec2go "$CACHE/ec2go"

# 3. Copy out/{annotation.annot,go_term2gene.tsv,go_term2name.tsv,summary.txt}
#    into docs/annotations/<organism>/ in this repo, alongside a short README
#    noting the proteome version and run date (mirror this directory's style).
```

Submit steps 1–2 via `sbatch` (see `scripts/slurm/e2e_pn40024.sbatch` or
`scripts/slurm/e2e.sbatch` as templates) rather than running on the login
node — DIAMOND-vs-nr and large index joins are not login-node-safe.

### Case 3 — Refresh the shared reference index itself
Only needed when you want to pick up newer UniProt/NCBI releases (this
affects *every* organism's coverage, takes hours, and downloads tens of GB):

```bash
sbatch /mnt/nfs3/sonegop/projects/b2gx/scripts/slurm/fetch_refdata.sbatch
```

Then redo Case 2 for each organism you want refreshed against the new index.

## Caveats

- **EC numbers** are included in `annotation.annot` (`EC:n.n.n.n` rows) but
  are not part of `go_term2gene.tsv`/`go_term2name.tsv` — those are GO-only,
  matching what `clusterProfiler::enricher()` expects for ORA on GO terms.
- **KEGG KO/pathway is intentionally empty** in all b2gx outputs — see the
  main `README.md` "Known limitations" section.
- This annotation merges multiple evidence sources (UniProt RefSeq +
  EMBL-CDS, NCBI gene2go) with different precision profiles. Per-protein
  concordance with a Blast2GO reference (where one exists) is documented in
  `docs/ACCEPTANCE_PN40024.md` — coverage roughly doubled but agreement on
  the newly-covered tail is noisier than on the original RefSeq-only core.
