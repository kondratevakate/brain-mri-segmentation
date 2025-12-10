#!/usr/bin/env bash
# Wait for sub-01 base to finish, then build bases for other SRPBS subjects (ATV/SWA).

set -euo pipefail

# Configurable paths.
SUBJECTS_DIR="${SUBJECTS_DIR:-/mnt/freesurfer_data/fs_longitudinal}"
SRC="${SRC:-/mnt/processed_subjects_data/srpbs_freesurfer8}"

# Subjects to process after sub-01 succeeds.
SUBJECT_IDS=(${SUBJECT_IDS:-02 03 04 05 06 07 08 09})

export SUBJECTS_DIR

BASE_WAIT="sub01_base_ATV_SWA"
BASE_LOG="$SUBJECTS_DIR/$BASE_WAIT/scripts/recon-all.log"

echo "[INFO] SUBJECTS_DIR=$SUBJECTS_DIR"
echo "[INFO] SRC=$SRC"
echo "[INFO] Waiting for $BASE_WAIT to finish cleanly..."

# Wait for sub01 base to finish successfully.
while :; do
  if find "$SUBJECTS_DIR/$BASE_WAIT/scripts" -maxdepth 1 -name "IsRunning.*" | grep -q .; then
    sleep 60
    continue
  fi
  if grep -q "exited with ERRORS" "$BASE_LOG"; then
    echo "[ERROR] Base $BASE_WAIT failed; aborting queue."
    exit 1
  fi
  if grep -q "finished without error" "$BASE_LOG"; then
    break
  fi
  sleep 60
done

echo "[INFO] $BASE_WAIT finished; starting queued bases."

for sid in "${SUBJECT_IDS[@]}"; do
  base="sub-${sid}_base_ATV_SWA"
  tp1="sub-${sid}_ses-siteATV"
  tp2="sub-${sid}_ses-siteSWA"

  echo "[SYNC] $tp1 / $tp2"
  rsync -a --ignore-existing "$SRC/$tp1/" "$SUBJECTS_DIR/$tp1/"
  rsync -a --ignore-existing "$SRC/$tp2/" "$SUBJECTS_DIR/$tp2/"

  echo "[RUN] recon-all -base $base -tp $tp1 -tp $tp2 -all"
  find "$SUBJECTS_DIR/$base/scripts" -maxdepth 1 -name "IsRunning.*" -delete 2>/dev/null || true
  recon-all -base "$base" -tp "$tp1" -tp "$tp2" -all || { echo "[ERROR] $base failed"; exit 1; }
done

echo "[DONE] All queued bases completed."
