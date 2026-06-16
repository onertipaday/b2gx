#!/usr/bin/env bash
#SBATCH --job-name=b2gx-image
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=8
#SBATCH --output=%x-%j.out
# Rebuild the b2gx apptainer image from the current source tree. %files copies
# "." (the build CWD) into /opt/b2gx, so this MUST run from the project root.
set -euo pipefail

PROJ=/mnt/nfs3/sonegop/projects/b2gx
SIF=/mnt/nfs3/sonegop/images/apptainer/b2gx.sif
cd "$PROJ"

apptainer build --force "$SIF" apptainer/b2gx.def

echo "=== rebuilt $SIF ==="
apptainer exec "$SIF" b2gx version
