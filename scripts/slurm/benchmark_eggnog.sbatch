#!/usr/bin/env bash
#SBATCH --job-name=b2gx-eggnog
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=32
#SBATCH --output=%x-%j.out
# eggNOG-mapper concordance benchmark. Prereqs: e2e.sbatch finished (produces
# annotation.annot), eggnog-mapper.sif, and the eggNOG data dir
# (/mnt/nfs3/sonegop/refdata/eggnog, ~50 GB via download_eggnog_data.py).
set -euo pipefail
exec bash /mnt/nfs3/sonegop/projects/b2gx/benchmark/run_eggnog.sh
