# PN40024 (*Vitis vinifera*) — b2gx GO Annotation

See `docs/annotations/README.md` for the general enrichment workflow (how to
use these files with clusterProfiler, and when to rerun anything). This file
covers only what's specific to this organism/run.

## Provenance

| | |
|---|---|
| Genome | PN40024 T2T 5.1, 48,976 proteins |
| b2gx run | 2026-06-17, HPC job 412100 |
| Reference index | `acc2go.parquet` rebuilt 2026-06-17 — UniProt idmapping (RefSeq + EMBL-CDS keying) merged with NCBI gene2accession/gene2go; 193.2M unique accessions |
| Coverage | 33,281 / 48,976 proteins annotated (**67.9%**), 145,568 GO assignments |
| vs Blast2GO reference | b2gx now exceeds Blast2GO's own coverage (54.2%) on this proteome — see `docs/ACCEPTANCE_PN40024.md` for the full concordance breakdown |
| EC numbers | 12,822 / 33,281 sequences (vs Blast2GO's 13,218) |

## Files in this directory

- `annotation.annot` — Blast2GO-style `seq_id\tGO:id` table (also carries
  `EC:n.n.n.n` rows).
- `go_term2gene.tsv` / `go_term2name.tsv` — clusterProfiler `TERM2GENE` /
  `TERM2NAME` inputs, GO-only.
- `summary.txt` — raw coverage stats for this run.
