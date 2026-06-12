#!/usr/bin/env bash
set -euo pipefail
SIF=/mnt/nfs3/sonegop/images/apptainer/eggnog-mapper.sif
DATA=/mnt/nfs3/sonegop/references/eggnog_db   # pre-existing emapperdb-5.0.2
PROJ=/mnt/nfs3/sonegop/projects/b2gx
FAA="$PROJ/references/GCF_023558375.1/protein.faa"
OUT="$PROJ/runs/chroococcidiopsis/eggnog"
BINDS="-B /mnt/nfs3/sonegop -B /mnt/scratch2/sonegop"
mkdir -p "$OUT"

# --go_evidence all keeps IEA-derived GO. b2gx transfers GO by homology (IEA-like),
# so eggNOG's default (non-electronic) would unfairly drop almost all bacterial GO.
apptainer exec $BINDS "$SIF" emapper.py \
  -i "$FAA" --itype proteins -o chroo --output_dir "$OUT" \
  --data_dir "$DATA" --cpu 32 --go_evidence all --override

# concordance_cli takes positional args: ANNOT EMAPPER OBO OUT
apptainer exec $BINDS --pwd /opt/b2gx /mnt/nfs3/sonegop/images/apptainer/b2gx.sif \
  /opt/b2gx/.venv/bin/python -m benchmark.concordance_cli \
  "$PROJ/runs/chroococcidiopsis/out/annotation.annot" \
  "$OUT/chroo.emapper.annotations" \
  /mnt/nfs3/sonegop/refdata/b2gx/go-basic.obo \
  "$OUT/concordance.tsv"
