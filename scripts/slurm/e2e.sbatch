#!/usr/bin/env bash
#SBATCH --job-name=b2gx-e2e
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=32
#SBATCH --output=%x-%j.out
# End-to-end acceptance on Chroococcidiopsis GCF_023558375.1.
# Prereqs: reference cache (fetch_refdata.sbatch) and a DIAMOND nr DB at
# /mnt/nfs3/sonegop/refdata/nr.dmnd (override NR in the script if elsewhere).
set -euo pipefail
exec bash /mnt/nfs3/sonegop/projects/b2gx/scripts/e2e_chroococcidiopsis.sh
