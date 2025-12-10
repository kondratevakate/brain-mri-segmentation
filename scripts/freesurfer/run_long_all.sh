#!/usr/bin/env bash
# Build a new base for sub-01 sessions and run recon-all -long on each.

set -euo pipefail

SUBJECTS_DIR="${SUBJECTS_DIR:-/mnt/freesurfer_data/fs_longitudinal}"
SRC="${SRC:-/mnt/processed_subjects_data/srpbs_freesurfer8}"
BASE="${BASE:-sub01_base_all}"
SESSIONS="${SESSIONS:-}"

export SUBJECTS_DIR

usage() {
  cat <<EOF
Usage: SUBJECTS_DIR=/mnt/fs BASE=sub01_base_all SRC=/mnt/... SESSIONS="sub-01_ses-..." $0
Environment variables:
  SUBJECTS_DIR   Destination FreeSurfer subjects dir (default: /mnt/freesurfer_data/fs_longitudinal)
  SRC            Source directory containing sub-01_* sessions (default: /mnt/processed_subjects_data/srpbs_freesurfer8)
  BASE           Name of the base subject to create (default: sub01_base_all)
  SESSIONS       Space-separated list of sessions; if empty, auto-detect sub-01_* in \$SRC
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Missing required command: $1"; exit 1; }
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage; exit 0
fi

require_cmd recon-all
require_cmd rsync
require_cmd tmux

if [ -z "$SESSIONS" ]; then
  SESSIONS=$(cd "$SRC" && ls -d sub-01_* 2>/dev/null | tr '\n' ' ' || true)
fi

if [ -z "$SESSIONS" ]; then
  echo "[ERROR] No sub-01 sessions found in $SRC"; exit 1
fi

echo "[INFO] SUBJECTS_DIR=$SUBJECTS_DIR"
echo "[INFO] SRC=$SRC"
echo "[INFO] BASE=$BASE"
echo "[INFO] SESSIONS=$SESSIONS"

mkdir -p "$SUBJECTS_DIR"

echo "[INFO] Syncing sessions to $SUBJECTS_DIR"
for ses in $SESSIONS; do
  [ -d "$SRC/$ses" ] || { echo "[ERROR] Missing session dir $SRC/$ses"; exit 1; }
  rsync -a --ignore-existing "$SRC/$ses/" "$SUBJECTS_DIR/$ses/" || { echo "[ERROR] rsync failed for $ses"; exit 1; }
done

BASE_DIR="$SUBJECTS_DIR/$BASE"
BASE_LOG="$BASE_DIR/scripts/recon-all.log"
TP_ARGS=$(printf " -tp %s" $SESSIONS)
SESSION_NAME="${SESSION_NAME:-fs_${BASE}}"

if [ -f "$BASE_LOG" ] && grep -q "finished without error" "$BASE_LOG"; then
  echo "[INFO] Base $BASE already finished; skipping base rebuild."
else
  echo "[INFO] Launching base build in tmux session $SESSION_NAME"
  tmux new-session -d -s "$SESSION_NAME" "recon-all -base ${BASE}${TP_ARGS} -all"
  echo "[INFO] Attach with: tmux attach -t $SESSION_NAME"
  echo "[INFO] Waiting for base to finish..."
  while :; do
    # Wait for scripts dir to appear on first pass
    if [ ! -d "$BASE_DIR/scripts" ]; then
      sleep 30; continue
    fi
    if find "$BASE_DIR/scripts" -maxdepth 1 -name 'IsRunning.*' | grep -q .; then
      sleep 60; continue
    fi
    if [ -f "$BASE_LOG" ] && grep -q "finished without error" "$BASE_LOG"; then
      break
    fi
    if [ -f "$BASE_LOG" ] && grep -q "exited with ERRORS" "$BASE_LOG"; then
      echo "[ERROR] Base log indicates errors: $BASE_LOG"; exit 1
    fi
    sleep 60
  done
  echo "[INFO] Base completed successfully."
fi

echo "[INFO] Running -long for each session"
for ses in $SESSIONS; do
  echo "[RUN] recon-all -long $ses $BASE -all"
  recon-all -long "$ses" "$BASE" -all || { echo "[ERROR] recon-all -long failed for $ses"; exit 1; }
done

echo "[DONE] All sub-01 long runs finished."
