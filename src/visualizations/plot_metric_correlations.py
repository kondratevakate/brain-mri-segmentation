"""
Plot correlations between segmentation metrics.

Creates scatter plots showing:
- Dice vs HD95 (expect negative correlation)
- Dice vs MAPE (expect weak correlation)

Purpose: Demonstrate that different metrics capture different aspects of variability.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr

# Styling
sns.set_style('whitegrid')
sns.set_context('paper', font_scale=1.2)


def compute_mape(df: pd.DataFrame) -> pd.Series:
    """Compute MAPE (Mean Absolute Percentage Error) for volume."""
    if 'percentage_vol_diff' in df.columns:
        return df['percentage_vol_diff'].abs() * 100
    elif 'volume_diff' in df.columns and 'volume1' in df.columns:
        return (df['volume_diff'].abs() / df['volume1']) * 100
    else:
        raise ValueError("Cannot compute MAPE: missing required columns")


def plot_metric_correlations(df: pd.DataFrame, output_path: Path, title_prefix: str = ""):
    """
    Create correlation scatter plots for metrics.

    Args:
        df: DataFrame with columns: dice, hd95, and volume data for MAPE
        output_path: Path to save figure
        title_prefix: Optional prefix for plot titles (e.g., "SIMON" or "SRPBS")
    """
    # Ensure MAPE column exists
    df = df.copy()
    df['mape'] = compute_mape(df)

    # Filter valid data
    df = df.dropna(subset=['dice', 'hd95', 'mape'])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Dice vs HD95
    ax1 = axes[0]
    valid_mask1 = (df['dice'] > 0) & (df['hd95'] < df['hd95'].quantile(0.99))
    data1 = df[valid_mask1]

    sns.scatterplot(data=data1, x='dice', y='hd95', alpha=0.4, s=20, ax=ax1)

    rho1, p1 = spearmanr(data1['dice'], data1['hd95'])
    p_str1 = f"p < 0.001" if p1 < 0.001 else f"p = {p1:.3f}"

    ax1.set_xlabel('Dice Coefficient', fontsize=12)
    ax1.set_ylabel('HD95 (mm)', fontsize=12)
    ax1.set_title(f'{title_prefix}Dice vs HD95\n(Spearman r = {rho1:.3f}, {p_str1})', fontsize=11)

    # Add trend line
    z = np.polyfit(data1['dice'], data1['hd95'], 1)
    p_line = np.poly1d(z)
    x_line = np.linspace(data1['dice'].min(), data1['dice'].max(), 100)
    ax1.plot(x_line, p_line(x_line), 'r--', alpha=0.7, linewidth=2)

    # Panel 2: Dice vs MAPE
    ax2 = axes[1]
    valid_mask2 = (df['dice'] > 0) & (df['mape'] < df['mape'].quantile(0.99))
    data2 = df[valid_mask2]

    sns.scatterplot(data=data2, x='dice', y='mape', alpha=0.4, s=20, ax=ax2)

    rho2, p2 = spearmanr(data2['dice'], data2['mape'])
    p_str2 = f"p < 0.001" if p2 < 0.001 else f"p = {p2:.3f}"

    ax2.set_xlabel('Dice Coefficient', fontsize=12)
    ax2.set_ylabel('Volume MAPE (%)', fontsize=12)
    ax2.set_title(f'{title_prefix}Dice vs Volume MAPE\n(Spearman r = {rho2:.3f}, {p_str2})', fontsize=11)

    # Add trend line
    z2 = np.polyfit(data2['dice'], data2['mape'], 1)
    p_line2 = np.poly1d(z2)
    x_line2 = np.linspace(data2['dice'].min(), data2['dice'].max(), 100)
    ax2.plot(x_line2, p_line2(x_line2), 'r--', alpha=0.7, linewidth=2)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved figure to {output_path}")

    return {
        'dice_vs_hd95': {'rho': rho1, 'p': p1, 'n': len(data1)},
        'dice_vs_mape': {'rho': rho2, 'p': p2, 'n': len(data2)}
    }


def main():
    parser = argparse.ArgumentParser(description='Plot metric correlations')
    parser.add_argument('--simon', type=str, default='data/simon_freesurfer.csv',
                        help='Path to SIMON CSV')
    parser.add_argument('--srpbs', type=str, default='data/cortical_all_sub_session_metrics.csv',
                        help='Path to SRPBS CSV')
    parser.add_argument('--output', type=str, default='outputs/figures/metric_correlations.pdf',
                        help='Output PDF path')
    parser.add_argument('--combined', action='store_true',
                        help='Create single combined plot instead of separate plots')
    args = parser.parse_args()

    output_path = Path(args.output)

    # Load and combine datasets
    print(f"Loading SIMON data from {args.simon}...")
    simon_df = pd.read_csv(args.simon)
    simon_df['dataset'] = 'SIMON (within-scanner)'

    print(f"Loading SRPBS data from {args.srpbs}...")
    srpbs_df = pd.read_csv(args.srpbs)
    srpbs_df['dataset'] = 'SRPBS (cross-scanner)'

    if args.combined:
        # Combined plot
        combined_df = pd.concat([simon_df, srpbs_df], ignore_index=True)
        results = plot_metric_correlations(combined_df, output_path, title_prefix="Combined: ")
        print(f"\nCorrelation results (combined):")
        for name, r in results.items():
            print(f"  {name}: r = {r['rho']:.3f}, p = {r['p']:.4f}, n = {r['n']}")
    else:
        # Separate plots per dataset
        print("\nCreating SIMON plot...")
        simon_output = output_path.with_stem(output_path.stem + "_simon")
        simon_results = plot_metric_correlations(simon_df, simon_output, title_prefix="SIMON: ")

        print("\nCreating SRPBS plot...")
        srpbs_output = output_path.with_stem(output_path.stem + "_srpbs")
        srpbs_results = plot_metric_correlations(srpbs_df, srpbs_output, title_prefix="SRPBS: ")

        # Also create combined
        print("\nCreating combined plot...")
        combined_df = pd.concat([simon_df, srpbs_df], ignore_index=True)
        combined_results = plot_metric_correlations(combined_df, output_path, title_prefix="")

        print("\n=== Correlation Summary ===")
        print("\nSIMON (within-scanner):")
        for name, r in simon_results.items():
            print(f"  {name}: r = {r['rho']:.3f}, p = {r['p']:.4f}, n = {r['n']}")

        print("\nSRPBS (cross-scanner):")
        for name, r in srpbs_results.items():
            print(f"  {name}: r = {r['rho']:.3f}, p = {r['p']:.4f}, n = {r['n']}")

        print("\nCombined:")
        for name, r in combined_results.items():
            print(f"  {name}: r = {r['rho']:.3f}, p = {r['p']:.4f}, n = {r['n']}")


if __name__ == '__main__':
    main()
