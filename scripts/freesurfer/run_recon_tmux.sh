#!/usr/bin/env bash
# Launch recon-all in a tmux session so it survives terminal closes.

set -euo pipefail

BASE_NAME="${BASE_NAME:-simonBase_iso1mm}"
TP_ARGS="${TP_ARGS:--tp ses-011 -tp ses-032 -tp ses-033}"
SESSION_NAME="${SESSION_NAME:-fs_${BASE_NAME}}"
export SUBJECTS_DIR="${SUBJECTS_DIR:-/mnt/freesurfer_data/fs_longitudinal}"

# Target recon-all command; override RECON_CMD directly if you want full control.
RECON_CMD=${RECON_CMD:-"recon-all -base ${BASE_NAME} ${TP_ARGS} -all"}

BASE_DIR="$SUBJECTS_DIR/${BASE_NAME}"
ISRUN="$BASE_DIR/scripts"

# Clean stale IsRunning markers (harmless before a restart)
if [ -d "$ISRUN" ]; then
  find "$ISRUN" -maxdepth 1 -name 'IsRunning.*' -delete 2>/dev/null || true
fi

echo "Using SUBJECTS_DIR=$SUBJECTS_DIR"
echo "Base name: $BASE_NAME"
echo "Starting tmux session: $SESSION_NAME"
echo "Command: $RECON_CMD"

# Start or reuse the tmux session
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  tmux send-keys -t "$SESSION_NAME" "$RECON_CMD" C-m
else
  tmux new-session -d -s "$SESSION_NAME" "$RECON_CMD"
fi

echo "Attach with: tmux attach -t $SESSION_NAME"
echo "Detach with: Ctrl-b d"
echo "Log: $BASE_DIR/scripts/recon-all.log"
