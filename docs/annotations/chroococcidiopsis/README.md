# Chroococcidiopsis `GCF_023558375.1` — b2gx GO Annotation

See `docs/annotations/README.md` for the general enrichment workflow (how to
use these files with clusterProfiler, and when to rerun anything). This file
covers only what's specific to this organism/run.

## Provenance

| | |
|---|---|
| Genome | `GCF_023558375.1`, 5,627 RefSeq proteins |
| b2gx run | 2026-06-17, HPC job 412099 |
| Reference index | `acc2go.parquet` rebuilt 2026-06-17 — UniProt idmapping (RefSeq + EMBL-CDS keying) merged with NCBI gene2accession/gene2go; 193.2M unique accessions |
| Coverage | 3,370 / 5,627 proteins annotated (**59.9%**), 10,532 GO assignments |
| EC numbers | 1,682 sequences |

Coverage lift here is modest (was 57.0% / 0.102 `coverage_resolved_fraction`
before this index expansion, now 59.9% / 0.125) — most bacterial RefSeq
accessions were already resolvable via UniProt idmapping; see
`docs/ACCEPTANCE.md` for the original eggNOG-mapper concordance benchmark
(not rerun against the expanded index — the GO-set composition shifted only
slightly for this organism).

## Files in this directory

- `annotation.annot` — Blast2GO-style `seq_id\tGO:id` table (also carries
  `EC:n.n.n.n` rows).
- `go_term2gene.tsv` / `go_term2name.tsv` — clusterProfiler `TERM2GENE` /
  `TERM2NAME` inputs, GO-only.
- `summary.txt` — raw coverage stats for this run.
