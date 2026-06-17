# b2gx Acceptance Run — Chroococcidiopsis `GCF_023558375.1`

End-to-end acceptance + eggNOG-mapper concordance benchmark, run on the HPC
cluster (SLURM `cpu` partition) on 2026-06-12.

## Inputs & reference data

| Item | Value |
|---|---|
| Query proteins | `GCF_023558375.1` (Chroococcidiopsis), 5,627 RefSeq proteins |
| Search DB | NCBI **nr** → DIAMOND `nr.dmnd` (346 GB), `diamond blastp` |
| acc→GO map | UniProt `idmapping_selected.tab.gz` → `acc2go.parquet` (RefSeq key) |
| GO DAG | `go-basic.obo` |
| EC | GO `ec2go` |
| Benchmark | eggNOG-mapper 2.1.13, **emapperdb-5.0.2**, `--go_evidence all` |

## End-to-end result

| Metric | Value |
|---|---|
| Sequences annotated (≥1 GO) | **3,207 / 5,627** (57%) |
| Total GO assignments | 9,810 |
| `coverage_resolved_fraction` | **0.102** |
| GO by namespace (BP / MF / CC) | 2,591 / 5,294 / 1,813 |
| EC | wired (via `ec2go`) |
| KEGG KO/pathway | empty by design (descoped — see README) |

**Coverage is source-limited, not a bug.** Subject and index accessions are both
versioned and match (a resolvable `WP_…` maps correctly), but of 70,144 unique
RefSeq subject accessions only **12,509 (17.8%)** appear in UniProt idmapping, and
the ~53k GenBank-type subjects (e.g. `AAT41948.1`) are not keyed at all. Roadmap
fix: NCBI `gene2accession → gene2go` supplement (see README "Known limitations").

## Update 2026-06-17 — expanded reference index

Rebuilt `acc2go.parquet` to also key UniProt idmapping on the EMBL-CDS
(GenBank-accession) column and merge in an NCBI `gene2accession → gene2go`
supplement (193.2M unique accessions vs 56.4M before — 3.4×). Rerun on the
same DIAMOND hits (job 412099):

| Metric | Before | After |
|---|---|---|
| Sequences annotated (≥1 GO) | 3,207 / 5,627 (57.0%) | **3,370 / 5,627 (59.9%)** |
| Total GO assignments | 9,810 | 10,532 |
| `coverage_resolved_fraction` | 0.102 | **0.125** |
| Sequences with EC | unverified pre-fix | 1,682 |

Modest lift for this organism — most bacterial RefSeq accessions were already
resolvable via UniProt idmapping alone, so the gene2go/EMBL-CDS supplement
helps less here than for eukaryotic GenBank-style accessions (see the much
larger PN40024 lift in `docs/ACCEPTANCE_PN40024.md`). eggNOG-mapper
concordance below was not rerun against the expanded index. Ready-to-use
annotation outputs (Blast2GO-style `.annot` + clusterProfiler tables) for
this run are saved at `docs/annotations/chroococcidiopsis/`.

## eggNOG-mapper concordance

eggNOG and b2gx use different evidence (orthology vs homology-transfer), so this
measures **concordance, not identity** (design §benchmark). GO sets are propagated
to ancestors before comparison (ancestor-aware Jaccard).

| Metric | Value |
|---|---|
| b2gx proteins with GO | 3,266 |
| eggNOG proteins with GO (`--go_evidence all`) | 940 |
| Proteins where **both** assign GO | 940 |
| Mean ancestor-aware Jaccard (overlap) | **0.467** |
| Median / p25 / p75 (overlap) | 0.519 / 0.342 / 0.612 |
| Mean Jaccard over all b2gx-annotated | 0.134 |

**Reading.** Where both tools make GO calls, they agree at a median ancestor-aware
Jaccard of ~0.52 — the same biological neighborhood, as expected for independent
evidence. b2gx has broader GO coverage here (3,266 vs 940); eggNOG's GO is sparse
for this organism even with all evidence (it is richer in COG/KEGG_ko). The
all-protein mean (0.134) is dragged down by the many proteins eggNOG leaves
GO-unannotated. The first benchmark pass reported 0.043 only because emapper's
default `--go_evidence non-electronic` dropped nearly all (IEA) bacterial GO
(408/5,258 proteins); `--go_evidence all` is required for a fair comparison.

## Reproduce

```bash
# on the cluster, from /mnt/nfs3/sonegop/projects/b2gx
sbatch scripts/slurm/fetch_refdata.sbatch     # reference cache
sbatch scripts/slurm/build_nr.sbatch          # nr.dmnd on scratch2
sbatch scripts/slurm/e2e.sbatch               # DIAMOND vs nr -> b2gx run
sbatch scripts/slurm/benchmark_eggnog.sbatch  # eggNOG concordance
```
