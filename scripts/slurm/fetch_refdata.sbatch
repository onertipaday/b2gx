#!/usr/bin/env bash
#SBATCH --job-name=b2gx-fetch
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=8
#SBATCH --output=%x-%j.out
# Build the b2gx reference cache (go-basic.obo, interpro2go, ec2go, and the
# heavy idmapping_selected.tab.gz -> acc2go.parquet index). Needs internet on
# the node (cpu partition). Hours + tens of GB of transient download.
set -euo pipefail

SIF=/mnt/nfs3/sonegop/images/apptainer/b2gx.sif
CACHE=/mnt/nfs3/sonegop/refdata/b2gx
PROJ=/mnt/nfs3/sonegop/projects/b2gx

# b2gx.sif's baked-in src predates the gene2go/EMBL-CDS index expansion; bind
# the current source tree over it (editable install) until the image is
# rebuilt via build_image.sbatch.
apptainer exec -B /mnt/nfs3/sonegop -B "$PROJ/src:/opt/b2gx/src" "$SIF" \
  b2gx fetch --cache-dir "$CACHE"

echo "=== reference cache ready in $CACHE ==="
ls -lh "$CACHE"
