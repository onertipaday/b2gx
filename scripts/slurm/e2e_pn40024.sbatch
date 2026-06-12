#!/usr/bin/env bash
#SBATCH --job-name=b2gx-pn40024
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=32
#SBATCH --output=%x-%j.out
# End-to-end b2gx run on Vitis vinifera PN40024 (T2T 5.1, 48,976 proteins),
# followed by concordance against the Blast2GO reference annotation.
set -euo pipefail
PROJ=/mnt/nfs3/sonegop/projects/b2gx
bash "$PROJ/scripts/e2e_pn40024.sh"
bash "$PROJ/benchmark/run_blast2go_concordance.sh"
