# b2gx vs Blast2GO — *Vitis vinifera* PN40024 (T2T 5.1)

Second acceptance run: b2gx end-to-end on the grapevine reference proteome,
compared against an existing **Blast2GO** annotation of the same proteins. Run on
the HPC cluster (SLURM `cpu` partition), 2026-06-12, job 412003 (GO/coverage);
EC re-run 2026-06-16, job 412050 after `parse_ec2go` inversion fix (commit 74c4ef3).

## Inputs

| Item | Value |
|---|---|
| Genome | `T2T_ref.fasta` (20 chromosomes) |
| Annotation | `PN40024_5.1_on_T2T_ref.gff3` (47,971 genes / 48,976 mRNAs) |
| Proteins | `gffread -y` → 48,976 proteins, renamed `<mRNA>_CDS1.prot` to match Blast2GO IDs |
| Search DB | NCBI **nr** → DIAMOND `nr.dmnd` (371 GB), `diamond blastp` (default sensitivity) |
| acc→GO map | UniProt `idmapping_selected.tab.gz` → `acc2go.parquet` (RefSeq key) |
| GO DAG | `go-basic.obo` |
| Reference | `PN40024_T2T_5.1_ref_blast2go.annot` (Blast2GO: blastp-vs-nr + InterProScan + EC) |

ID alignment is exact: all 26,548 Blast2GO-annotated sequences are among the
48,976 b2gx proteins (100% intersection), so concordance compares like-for-like.

## Coverage (protein-level, of 48,976 proteins)

| Metric | b2gx | Blast2GO |
|---|---|---|
| Proteins with DIAMOND hits | 42,227 (86.2%) | — |
| Proteins annotated (≥1 GO) | **14,890 (30.4%)** | **26,548 (54.2%)** |
| Total GO assignments | 56,643 | 80,536 |
| GO by namespace (BP / MF / CC) | 17,587 / 23,385 / 15,342 | — |
| EC numbers | **5,051 seqs / 13,986 lines / 1,008 unique** | 13,218 |
| InterPro domains | 0 (no InterProScan run) | present |
| `coverage_resolved_fraction` | 0.059 | — |

## Concordance (ancestor-aware GO Jaccard)

GO sets propagated to ancestors before comparison. Independent evidence, so this
measures **concordance, not identity**.

| Category | Count |
|---|---|
| Proteins both annotate | **13,536** |
| b2gx-only | 1,354 |
| Blast2GO-only | 13,012 |

| Jaccard (13,536 both-annotated) | Value |
|---|---|
| Mean / median | **0.411 / 0.429** |
| p25 / p75 | 0.136 / 0.647 |
| ≥ 0.5 | 5,790 (43%) |
| ≥ 0.8 | 1,490 (11%) |
| Exact 0 | 2,497 (18%) |
| Mean over all b2gx-annotated | 0.373 |

**Reading.** Where both tools annotate, the median ancestor-aware Jaccard is
~0.43 — the same biological neighborhood, consistent with the eggNOG-mapper
benchmark on Chroococcidiopsis (0.47). The 18% exact-zero tail is mostly proteins
where the two tools transferred GO from different evidence (e.g. b2gx homology vs
Blast2GO InterPro-domain GO) with no ancestor overlap.

## Why b2gx annotates fewer proteins than Blast2GO

b2gx covers 56% of what Blast2GO annotates (14,890 vs 26,548). Three causes, in
order of impact:

1. **acc→GO ceiling (largest).** 429,912 of 456,910 distinct nr subject
   accessions (94%) do not resolve to any GO term. nr returns many
   GenBank/PDB/non-RefSeq subjects (`1WH9_A`, `KAG…`, `WKA…`) that the
   RefSeq-keyed `acc2go.parquet` cannot map. Same limitation documented for the
   Chroococcidiopsis run; roadmap fix is the NCBI `gene2accession → gene2go`
   supplement plus keying on the idmapping EMBL-CDS (GenBank) column.
2. **No InterProScan.** Blast2GO merges InterProScan domain GO (the reference
   `.tsv` carries an `InterPro GO ID` column); this run was homology-only
   (`interpro` empty), so b2gx misses proteins whose only GO comes from domains.
3. **EC gap narrowed.** After the `parse_ec2go` fix, b2gx assigns EC to 5,051
   sequences (10.3% of proteome, 1,008 unique EC numbers, 13,986 `.annot` lines)
   vs Blast2GO's 13,218. The remaining gap is the same acc→GO ceiling: proteins
   with no resolved GO also receive no EC via `ec2go`; InterProScan-derived EC
   (present in the Blast2GO reference) is outside scope.

## Update 2026-06-17 — expanded reference index

Rebuilt `acc2go.parquet` to also key UniProt idmapping on the EMBL-CDS
(GenBank-accession) column and merge in an NCBI `gene2accession → gene2go`
supplement (193.2M unique accessions vs 56.4M before — 3.4×). This directly
targets cause #1 above. Rerun on the same DIAMOND hits (job 412100):

| Metric | Before | After | Blast2GO |
|---|---|---|---|
| Proteins annotated (≥1 GO) | 14,890 (30.4%) | **33,281 (67.9%)** | 26,548 (54.2%) |
| Total GO assignments | 56,643 | 145,568 | 80,536 |
| `coverage_resolved_fraction` | 0.059 | **0.614** | — |
| EC numbers | 5,051 seqs / 1,008 unique | **12,822 seqs / 1,352 unique** | 13,218 |

**b2gx now exceeds Blast2GO's own coverage** on this proteome (67.9% vs
54.2%) — the EMBL-CDS keying resolved most of the GenBank-style (`KAG…`,
`AAT…`) subjects that dominated the unresolved tail.

### Concordance, recomputed (both-annotate subset, not the full union)

| Category | Before | After |
|---|---|---|
| Both annotate | 13,536 | **26,230** (1.9×) |
| b2gx-only | 1,354 | 7,051 |
| Blast2GO-only | 13,012 | **318** (b2gx now covers 98.8% of what Blast2GO covers) |

| Jaccard (both-annotated) | Before | After |
|---|---|---|
| Mean / median | 0.411 / 0.429 | **0.410 / 0.450** |
| p25 / p75 | 0.136 / 0.647 | 0.110 / 0.650 |
| ≥ 0.5 | 43% | 44.9% |
| ≥ 0.8 | 11% | 10.1% |
| Exact 0 | 18% | 23.0% |

**Reading.** Concordance quality on the overlapping set is essentially
**unchanged** — adding ~12,700 more both-annotated proteins did not dilute
agreement. The expanded index closes coverage without trading away accuracy.
The earlier draft of this update incorrectly computed these stats over the
full union file (33,599 rows, b2gx ∪ Blast2GO) instead of filtering to
`n_b2gx > 0 AND n_eggnog > 0`; that error has been corrected here.

Ready-to-use annotation outputs (Blast2GO-style `.annot` + clusterProfiler
tables) for this run are saved at `docs/annotations/pn40024/`.

## Reproduce

```bash
# on the cluster, from /mnt/nfs3/sonegop/projects/b2gx
#  - proteins: gffread -y from T2T_ref.fasta + PN40024_5.1_on_T2T_ref.gff3,
#    headers renamed <mRNA>_CDS1.prot
sbatch scripts/slurm/fetch_refdata.sbatch # reference cache (RefSeq+EMBL-CDS+gene2go)
sbatch scripts/slurm/e2e_pn40024.sbatch   # DIAMOND vs nr -> b2gx run -> concordance
# outputs: runs/pn40024/{hits.tsv, out/, concordance_vs_blast2go.tsv}
```
