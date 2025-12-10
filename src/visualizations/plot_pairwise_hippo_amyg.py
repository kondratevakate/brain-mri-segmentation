#!/usr/bin/env python3
"""
Plot hippocampus/amygdala volume stability from pairwise metrics CSV (session1/session2, label, volume1/2, subject).
- Assumes volumes in mm^3; converts to mL.
- Builds per-session volumes by taking median across all pair appearances.
Usage:
    PYTHONPATH="." python3 src/visualizations/plot_pairwise_hippo_amyg.py \
      --csv data/srpbs_freesurfer8_metrics.csv \
      --subject sub-01 \
      --out figures/srpbs_fs8_hippo_amyg.png \
      --first-same 5
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

LABELS = {17: "LH", 53: "RH", 18: "LA", 54: "RA"}
PALETTE = {"LH": "#1f77b4", "RH": "#ff7f0e", "LA": "#2ca02c", "RA": "#d62728"}
HIPPO_YLIM = (3.3, 5.7)
AMYG_YLIM = (1.25, 2.15)
START_OFFSET = 0  # display session indices starting from 0; early ticks can be empty if no data
# fixed marker half-length in mL to keep consistent across panels
MARK_HALF_LEN = 0.05


def build_tidy(df: pd.DataFrame, subject: str) -> pd.DataFrame:
    df = df[df["subject"] == subject]
    df = df[df["label"].isin(LABELS)]
    if df.empty:
        raise SystemExit(f"No rows for subject {subject} with target labels")
    tidy = pd.concat([
        df[["session1", "label", "volume1"]].rename(columns={"session1": "session", "volume1": "volume"}),
        df[["session2", "label", "volume2"]].rename(columns={"session2": "session", "volume2": "volume"}),
    ])
    # если есть label_name, можно использовать, но для простоты держим LH/RH/LA/RA
    tidy = tidy.groupby(["label", "session"], as_index=False)["volume"].median()
    tidy["structure"] = tidy["label"].map(LABELS)
    tidy["volume_ml"] = tidy["volume"] / 1000.0  # мм^3 -> mL
    return tidy


def plot_panel(ax, tidy: pd.DataFrame, labels, title: str, first_same: int):
    session_order = sorted(tidy["session"].unique())
    idx_map = {s: i for i, s in enumerate(session_order)}
    tidy = tidy.copy()
    tidy["session_idx"] = tidy["session"].map(idx_map)

    vmin, vmax = tidy["volume_ml"].min(), tidy["volume_ml"].max()

    bbox_x = len(session_order) + 0.8

    for lbl in labels:
        s = tidy[tidy["label"] == lbl]
        short = LABELS[lbl]
        ax.vlines(s["session_idx"], s["volume_ml"] - MARK_HALF_LEN, s["volume_ml"] + MARK_HALF_LEN,
                  colors=PALETTE[short], linewidth=2, zorder=3)

    box_data = [tidy[tidy["label"] == lbl]["volume_ml"] for lbl in labels]
    ax.boxplot(box_data, positions=np.arange(len(labels)) + bbox_x,
               widths=0.4, patch_artist=True,
               boxprops=dict(facecolor="white", edgecolor="black"),
               medianprops=dict(color="black"),
               whiskerprops=dict(color="black"),
               capprops=dict(color="black"),
               flierprops=dict(markerfacecolor="white", markeredgecolor="black", markersize=5))

    if first_same > 0:
        ax.axvspan(-0.5, first_same - 0.5, color="0.85", zorder=0, lw=0)

    xticks = list(range(len(session_order))) + list(np.arange(len(labels)) + bbox_x)
    xticklabels = [str(i + START_OFFSET) if i % 2 == 0 else "" for i in range(len(session_order))] + [LABELS[l] for l in labels]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)
    ax.set_xlim(-0.75, bbox_x + len(labels) - 0.4)
    if title.lower().startswith("hippo"):
        ax.set_ylim(*HIPPO_YLIM)
    elif title.lower().startswith("amyg"):
        ax.set_ylim(*AMYG_YLIM)
    else:
        pad = 0.05 * (vmax - vmin) if vmax > vmin else 0.1
        ax.set_ylim(vmin - pad, vmax + pad)
    ax.set_xlabel("Test / Retest")
    ax.set_ylabel("Volume (mL)")
    ax.set_title(title)

    stats = []
    for lbl in labels:
        vals = tidy[tidy["label"] == lbl]["volume_ml"]
        stats.append((LABELS[lbl], vals.mean(), vals.std(ddof=0)))
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="pairwise metrics CSV")
    parser.add_argument("--subject", required=True, help="subject id to plot (e.g., sub-01)")
    parser.add_argument("--out", required=True, help="output PNG path")
    parser.add_argument("--first-same", type=int, default=5, help="number of initial sessions on same scanner")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    tidy = build_tidy(df, args.subject)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    stats1 = plot_panel(axes[0], tidy, [17, 53], "Hippocampus", args.first_same)
    stats2 = plot_panel(axes[1], tidy, [18, 54], "Amygdala", args.first_same)
    stats = stats1 + stats2

    handles = []
    labels = []
    for short, mu, sd in stats:
        handles.append(plt.Line2D([0], [0], color=PALETTE[short], lw=2.2,
                                  marker='s', markersize=6, linestyle='-'))
        labels.append(f"{short}: {mu:.2f} ({sd:.2f}) mL")
    if args.first_same > 0:
        start_label = START_OFFSET
        end_label = START_OFFSET + args.first_same - 1
        handles.append(plt.Rectangle((0, 0), 1, 1, color="0.85",
                                     label=f"Same Scanner (Tests {start_label}–{end_label})"))
        labels.append(f"Same Scanner (Tests {start_label}–{end_label})")

    fig.legend(handles=handles, labels=labels, loc="upper right",
               bbox_to_anchor=(1.0, 1.02), frameon=True)
    fig.tight_layout(rect=(0, 0, 0.82, 0.95))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    main()
