#!/usr/bin/env bash
#SBATCH --job-name=b2gx-eggnog-setup
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=8
#SBATCH --output=%x-%j.out
# Pull the eggNOG-mapper image and fetch its reference data (~12 GB compressed,
# ~50 GB unpacked) to scratch2. Independent of the nr build.
#
# NOTE: eggnog-mapper's download_eggnog_data.py hardcodes the now-dead host
# eggnogdb.embl.de (no DNS). The data lives on eggnog5.embl.de, so we download
# the diamond-mode files directly instead of using that script.
set -euo pipefail

REF=/mnt/scratch2/sonegop/references
IMG=/mnt/nfs3/sonegop/images/apptainer
EGGNOG_SIF="$IMG/eggnog-mapper.sif"
DATA="$REF/eggnog"
BASE=http://eggnog5.embl.de/download/emapperdb-5.0.2
mkdir -p "$DATA" "$IMG"

if [[ ! -s "$EGGNOG_SIF" ]]; then
  apptainer pull "$EGGNOG_SIF" \
    docker://quay.io/biocontainers/eggnog-mapper:2.1.13--pyhdfd78af_2
fi

cd "$DATA"
# drop any 0-byte remnants from the failed run
find . -maxdepth 1 -type f -size 0 -delete

# eggnog5 drops large connections mid-transfer; wget -c resumes partials and
# --tries=0 retries indefinitely so a dropped connection doesn't fail the job.
get() { wget -c --tries=0 --waitretry=10 --retry-connrefused --read-timeout=120 -O "$2" "$1"; }

# eggnog.db (annotations)
if [[ ! -s eggnog.db ]]; then
  get "$BASE/eggnog.db.gz" eggnog.db.gz
  gunzip -f eggnog.db.gz
fi
# eggnog_proteins.dmnd (diamond seed db)
if [[ ! -s eggnog_proteins.dmnd ]]; then
  get "$BASE/eggnog_proteins.dmnd.gz" eggnog_proteins.dmnd.gz
  gunzip -f eggnog_proteins.dmnd.gz
fi
# eggnog.taxa.db + traverse pkl
if [[ ! -s eggnog.taxa.db ]]; then
  get "$BASE/eggnog.taxa.tar.gz" eggnog.taxa.tar.gz
  tar -zxf eggnog.taxa.tar.gz && rm -f eggnog.taxa.tar.gz
fi

echo "=== eggNOG data ready in $DATA ==="
ls -lh "$DATA"
