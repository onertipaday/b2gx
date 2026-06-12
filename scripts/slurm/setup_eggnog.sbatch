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

# eggnog5 drops large connections mid-transfer. Start each file clean (a stale
# cross-tool partial makes wget -c wrongly conclude "already fully retrieved"),
# then loop wget -c until the local size matches the server's Content-Length.
get() {
  local url=$1 out=$2 i exp got
  exp=$(curl -sIL --max-time 30 "$url" \
        | awk 'BEGIN{IGNORECASE=1}/^content-length:/{v=$2} END{gsub(/\r/,"",v);print v}')
  [[ -z "$exp" ]] && { echo "no Content-Length for $url"; return 1; }
  rm -f "$out"
  for i in $(seq 1 50); do
    wget -c --read-timeout=120 -O "$out" "$url" || true
    got=$(stat -c%s "$out" 2>/dev/null || echo 0)
    [[ "$got" == "$exp" ]] && { echo "$out complete ($got bytes)"; return 0; }
    echo "attempt $i: $got/$exp bytes for $out; retrying"; sleep 10
  done
  return 1
}

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
