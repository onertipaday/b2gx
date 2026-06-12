#!/usr/bin/env bash
#SBATCH --job-name=b2gx-eggnog-setup
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=8
#SBATCH --output=%x-%j.out
# Pull the eggNOG-mapper image and download its reference data (~50 GB) to
# scratch2. Independent of the nr build; can run in parallel.
set -euo pipefail

REF=/mnt/scratch2/sonegop/references
IMG=/mnt/nfs3/sonegop/images/apptainer
EGGNOG_SIF="$IMG/eggnog-mapper.sif"
DATA="$REF/eggnog"
mkdir -p "$DATA" "$IMG"

if [[ ! -s "$EGGNOG_SIF" ]]; then
  apptainer pull "$EGGNOG_SIF" \
    docker://quay.io/biocontainers/eggnog-mapper:2.1.13--pyhdfd78af_2
fi

apptainer exec -B /mnt/scratch2/sonegop "$EGGNOG_SIF" \
  download_eggnog_data.py -y --data_dir "$DATA"

echo "=== eggNOG data ready in $DATA ==="
ls -lh "$DATA"
