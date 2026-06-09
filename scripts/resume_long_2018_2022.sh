#!/usr/bin/env bash
# Resume the FS7.4 longitudinal pipeline for the two VALID timepoints (2018, 2022).
# 2024 failed Talairach (quarantined as 2024_FAILED_talairach) and is excluded.
# Cross-sectional already done; this runs: -base kate_base -> -long (parallel).
# Stable location (main project) so it is NOT deleted out from under bash mid-run.
set -uo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

DATA="${DATA:?set DATA to the data root}"
LIC="${FS_LICENSE_FILE:?set FS_LICENSE_FILE}"
IMG="freesurfer/freesurfer:7.4.1"
SD="/data/reprocessed_2026/fs_long"
LOGD="$DATA/reprocessed_2026/logs"; mkdir -p "$LOGD"
BASE_ID="kate_base"; TPS=(2018 2022)

fs() {
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker run --rm --user root \
    -v "$DATA:/data" -v "$LIC:/fs_license/license.txt:ro" \
    -e FS_LICENSE=/fs_license/license.txt -e SUBJECTS_DIR="$SD" "$IMG" "$@"
}

# --- base template (barrier) ---
if [ -f "$DATA/reprocessed_2026/fs_long/$BASE_ID/scripts/recon-all.done" ]; then
  echo "[skip] base $(date +%T)"
else
  echo "[start] base $BASE_ID from ${TPS[*]} $(date +%T)"
  fs recon-all -base "$BASE_ID" -tp 2018 -tp 2022 -all -threads 4 \
    > "$LOGD/fs_base.log" 2>&1 \
    && echo "[done] base $(date +%T)" || { echo "[FAIL] base (see fs_base.log)"; exit 1; }
fi

# --- longitudinal pass, two timepoints in parallel ---
for s in "${TPS[@]}"; do
  lid="$s.long.$BASE_ID"
  [ -f "$DATA/reprocessed_2026/fs_long/$lid/scripts/recon-all.done" ] && { echo "[skip] long $s"; continue; }
  ( echo "[start] long $s $(date +%T)"
    fs recon-all -long "$s" "$BASE_ID" -all -threads 4 > "$LOGD/fs_long_${s}.log" 2>&1 \
      && echo "[done] long $s $(date +%T)" || echo "[FAIL] long $s" ) &
done
wait
echo "ALL DONE $(date +%T)  (base + long for 2018, 2022; 2024 excluded - Talairach failed)"
