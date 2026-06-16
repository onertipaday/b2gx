#!/usr/bin/env bash
# Concordance of the b2gx PN40024 run against the Blast2GO reference annotation.
set -euo pipefail
PROJ=/mnt/nfs3/sonegop/projects/b2gx
SIF=/mnt/nfs3/sonegop/images/apptainer/b2gx.sif
CACHE=/mnt/nfs3/sonegop/refdata/b2gx
OUT="$PROJ/runs/pn40024/out"
B2GX_ANNOT="$OUT/annotation.annot"
B2GO_ANNOT="$PROJ/references/PN40024/blast2go/PN40024_T2T_5.1_ref_blast2go.annot"
BINDS="-B /mnt/nfs3/sonegop -B /mnt/scratch2/sonegop"

# Run the image's venv python against the *deployed* benchmark/ (via cwd on -m),
# so a new CLI does not require rebuilding the image. b2gx resolves from the venv.
apptainer exec $BINDS --pwd "$PROJ" "$SIF" \
  /opt/b2gx/.venv/bin/python -m benchmark.concordance_annot_cli \
  "$B2GX_ANNOT" "$B2GO_ANNOT" "$CACHE/go-basic.obo" \
  "$PROJ/runs/pn40024/concordance_vs_blast2go.tsv"
