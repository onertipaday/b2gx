#!/usr/bin/env bash
# End-to-end acceptance run on Chroococcidiopsis GCF_023558375.1 (5,627 proteins).
# Runs on the HPC cluster (needs nr + the b2gx reference cache). CPU partition.
set -euo pipefail

SIF=/mnt/nfs3/sonegop/images/apptainer/b2gx.sif
CACHE=/mnt/nfs3/sonegop/refdata/b2gx
PROJ=/mnt/nfs3/sonegop/projects/b2gx
FAA="$PROJ/references/GCF_023558375.1/protein.faa"
WORK="$PROJ/runs/chroococcidiopsis"
NR=/mnt/nfs3/sonegop/refdata/nr.dmnd   # adjust if your DIAMOND nr DB lives elsewhere
mkdir -p "$WORK"

# 1. DIAMOND blastp vs nr (required columns incl. ppos, qcovhsp).
if [[ ! -s "$WORK/hits.tsv" ]]; then
  apptainer exec -B /mnt/nfs3/sonegop "$SIF" \
    diamond blastp -d "$NR" -q "$FAA" \
    -f 6 qseqid sseqid pident ppos length evalue bitscore qcovhsp \
    -o "$WORK/hits.tsv" -p 32 --quiet \
    || { echo "DIAMOND not in image or nr missing; produce $WORK/hits.tsv separately and re-run"; exit 1; }
fi

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

apptainer exec -B /mnt/nfs3/sonegop "$SIF" b2gx run \
  --config "$WORK/run.yaml" --obo "$CACHE/go-basic.obo" \
  --index "$CACHE/acc2go.parquet" --ec2go "$CACHE/ec2go"

echo "=== summary ==="
cat "$WORK/out/summary.txt"
