#!/usr/bin/env bash
set -euo pipefail
SIF=/mnt/nfs3/sonegop/images/apptainer/eggnog-mapper.sif
DATA=/mnt/nfs3/sonegop/refdata/eggnog
PROJ=/mnt/nfs3/sonegop/projects/b2gx
FAA="$PROJ/references/GCF_023558375.1/protein.faa"
OUT="$PROJ/runs/chroococcidiopsis/eggnog"
mkdir -p "$OUT"

apptainer exec -B /mnt/nfs3/sonegop "$SIF" emapper.py \
  -i "$FAA" --itype proteins -o chroo --output_dir "$OUT" \
  --data_dir "$DATA" --cpu 32 --override

apptainer exec -B /mnt/nfs3/sonegop /mnt/nfs3/sonegop/images/apptainer/b2gx.sif \
  python -m benchmark.concordance_cli \
  --annot "$PROJ/runs/chroococcidiopsis/out/annotation.annot" \
  --emapper "$OUT/chroo.emapper.annotations" \
  --obo /mnt/nfs3/sonegop/refdata/b2gx/go-basic.obo \
  --out "$OUT/concordance.tsv"
