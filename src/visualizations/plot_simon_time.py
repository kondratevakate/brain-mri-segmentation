#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

import argparse

CSV = "data/simon_fastserfer_non_reg.csv"
PHENO = "data/SIMON_pheno.csv"
OUT = "figures/simon_hippo_amyg_time.png"
TITLE_TAG = "FastSurfer non-registered"

TARGETS = {
    "Amygdala Volume Over Time": ["Left Amygdala", "Right Amygdala"],
    "Hippocampus Volume Over Time": ["Left Hippocampus", "Right Hippocampus"],
}
PALETTE = {
    "Left Amygdala": "#4C72B0",
    "Right Amygdala": "#C44E52",
    "Left Hippocampus": "#4C72B0",
    "Right Hippocampus": "#C44E52",
}

def ensure_time(df: pd.DataFrame, pheno_path: str) -> pd.DataFrame:
    """Ensure df has years_since_first using days_since_first or pheno dates."""
    if "days_since_first" in df.columns and not df["days_since_first"].isna().all():
        df["years_since_first"] = df["days_since_first"] / 365.25
        return df
    ph = pd.read_csv(pheno_path)
    ph["Session_idx"] = ph["Session"].astype(int)
    ph["Acquisition_date"] = pd.to_datetime(ph["Acquisition_date"], format="%m/%d/%y")
    t0 = ph["Acquisition_date"].min()
    ph["days_since_first"] = (ph["Acquisition_date"] - t0).dt.days
    df["session_num"] = df["session"].str.extract(r"ses-(\d+)", expand=False).astype(int)
    df = df.merge(
        ph[["Session_idx", "days_since_first"]],
        left_on="session_num", right_on="Session_idx",
        how="left", suffixes=("", "_ph")
    )
    if df["days_since_first"].isna().any():
        missing = df[df["days_since_first"].isna()]["session"].unique()
        raise SystemExit(f"No pheno date for sessions: {missing}")
    df["years_since_first"] = df["days_since_first"] / 365.25
    return df


def main():
    parser = argparse.ArgumentParser(description="Volume trajectories over time for hippocampus/amygdala.")
    parser.add_argument("--csv", default=CSV, help="input CSV with per-session volumes")
    parser.add_argument("--pheno", default=PHENO, help="pheno CSV with Session/Acquisition_date")
    parser.add_argument("--out", default=OUT, help="output PNG path")
    parser.add_argument("--title-tag", default=TITLE_TAG, help="tag appended to panel titles")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    df = df[df["structure_name"].isin(sum(TARGETS.values(), []))].copy()
    if df.empty:
        raise SystemExit("No rows after filtering target structures")

    if "days_since_first" in df.columns:
        df = df.drop(columns=["days_since_first"])
    df = ensure_time(df, args.pheno)

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    for ax, (title, structs) in zip(axes, TARGETS.items()):
        sub = df[df["structure_name"].isin(structs)]
        legend_entries = []
        for struct in structs:
            s = sub[sub["structure_name"] == struct]
            x, y = s["years_since_first"].values, s["volume_cm3"].values
            if len(np.unique(x)) >= 2:
                coef = np.polyfit(x, y, 1)
                y_pred = np.polyval(coef, x)
                ss_res = ((y - y_pred) ** 2).sum()
                ss_tot = ((y - y.mean()) ** 2).sum()
                r2 = 1 - ss_res/ss_tot if ss_tot else np.nan
            else:
                r2 = np.nan
            legend_entries.append((struct, r2))
            sns.regplot(
                data=s, x="years_since_first", y="volume_cm3",
                ax=ax, scatter_kws={"s": 28, "alpha": 0.8},
                line_kws={"lw": 2.2, "color": PALETTE[struct]},
                ci=80, color=PALETTE[struct],
            )
        ax.set_title(title, fontsize=12, pad=8)
        ax.set_ylabel("Volume (mL)")
        ax.set_xlabel("")  # clear regplot default label
        ax.legend(
            [plt.Line2D([0],[0], color=PALETTE[n], lw=2.2, marker='o', markersize=6, linestyle='-')
             for n,_ in legend_entries],
            [f"{n} (R²={r2:.3f})" for n,r2 in legend_entries],
            loc="upper left", frameon=True
        )

    axes[-1].set_xlabel("Years since first scan")
    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=300, bbox_inches="tight")
    print(f"Saved plot to {args.out}")

if __name__ == "__main__":
    main()
