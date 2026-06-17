#!/usr/bin/env bash
# End-to-end run on Vitis vinifera PN40024 (T2T 5.1, 48,976 proteins).
# DIAMOND blastp vs nr -> b2gx run. Mirrors the Chroococcidiopsis acceptance
# pipeline so results are directly comparable. CPU partition, no time limit.
set -euo pipefail

SIF=/mnt/nfs3/sonegop/images/apptainer/b2gx.sif
DIAMOND_SIF=/mnt/nfs3/sonegop/images/apptainer/diamond.sif
CACHE=/mnt/nfs3/sonegop/refdata/b2gx
PROJ=/mnt/nfs3/sonegop/projects/b2gx
FAA="$PROJ/references/PN40024/protein.faa"
WORK="$PROJ/runs/pn40024"
NR=/mnt/scratch2/sonegop/references/nr.dmnd
# b2gx.sif's baked-in src predates the gene2go/EMBL-CDS index expansion; bind
# the current source tree over it (editable install) until the image is
# rebuilt via build_image.sbatch.
BINDS="-B /mnt/nfs3/sonegop -B /mnt/scratch2/sonegop -B $PROJ/src:/opt/b2gx/src"
mkdir -p "$WORK"

# 1. DIAMOND blastp vs nr (same columns as the Chroococcidiopsis run).
if [[ ! -s "$WORK/hits.tsv" ]]; then
  apptainer exec $BINDS "$DIAMOND_SIF" \
    diamond blastp -d "$NR" -q "$FAA" \
    -f 6 qseqid sseqid pident ppos length evalue bitscore qcovhsp \
    -o "$WORK/hits.tsv" -p 32 --quiet \
    || { echo "DIAMOND failed or nr missing ($NR)"; exit 1; }
fi
echo "=== DIAMOND hits: $(wc -l < "$WORK/hits.tsv") rows, $(cut -f1 "$WORK/hits.tsv" | sort -u | wc -l) queries with hits ==="

# 2. b2gx run.
cat > "$WORK/run.yaml" <<YAML
query_fasta: $FAA
diamond_tsv: $WORK/hits.tsv
cache_dir: $CACHE
out_dir: $WORK/out
annotation:
  annotation_cutoff: 55
  go_weight: 5
YAML

apptainer exec $BINDS "$SIF" b2gx run \
  --config "$WORK/run.yaml" --obo "$CACHE/go-basic.obo" \
  --index "$CACHE/acc2go.parquet" --ec2go "$CACHE/ec2go"

echo "=== summary ==="
cat "$WORK/out/summary.txt"
