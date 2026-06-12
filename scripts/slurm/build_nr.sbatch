#!/usr/bin/env bash
#SBATCH --job-name=b2gx-nr
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=32
#SBATCH --output=%x-%j.out
# Download NCBI nr (FASTA) and build a DIAMOND database on scratch2.
# ~200 GB download + ~300 GB .dmnd; built under /mnt/scratch2/sonegop/references.
set -euo pipefail

REF=/mnt/scratch2/sonegop/references
IMG=/mnt/nfs3/sonegop/images/apptainer
DIAMOND_SIF="$IMG/diamond.sif"
NR_GZ="$REF/nr.gz"
NR_DB="$REF/nr"   # diamond appends .dmnd
mkdir -p "$REF" "$IMG"

# 1. DIAMOND image (biocontainer) — pull once if absent.
if [[ ! -s "$DIAMOND_SIF" ]]; then
  apptainer pull "$DIAMOND_SIF" docker://quay.io/biocontainers/diamond:2.2.1--he361c42_0
fi

# 2. Download nr.gz (resumable).
if [[ ! -s "$NR_GZ" ]]; then
  curl -L --fail -C - -o "$NR_GZ" \
    https://ftp.ncbi.nlm.nih.gov/blast/db/FASTA/nr.gz
fi

# 3. Build the DIAMOND db, then drop the 200 GB gz to reclaim space.
apptainer exec -B /mnt/scratch2/sonegop "$DIAMOND_SIF" \
  diamond makedb --in "$NR_GZ" -d "$NR_DB" -p "${SLURM_CPUS_PER_TASK:-32}"

rm -f "$NR_GZ"
echo "=== nr DIAMOND db ready: ${NR_DB}.dmnd ==="
ls -lh "${NR_DB}.dmnd"
