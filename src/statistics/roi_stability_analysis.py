"""
Analyze ROI stability: cortical vs subcortical, and dependency on ROI size.

Questions:
1. Are cortical or subcortical regions more stable across scanners?
2. Does stability depend on mean ROI volume?
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr, mannwhitneyu

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.regions import (
    CORTICAL_LABELS, SUBCORTICAL_LABELS,
    CORTICAL_AND_SUBCORTICAL_NAMES
)

sns.set_style('whitegrid')
sns.set_context('paper', font_scale=1.2)


def compute_mape(df: pd.DataFrame) -> pd.Series:
    """Compute MAPE for volume."""
    if 'percentage_vol_diff' in df.columns:
        return df['percentage_vol_diff'].abs() * 100
    elif 'volume_diff' in df.columns and 'volume1' in df.columns:
        return (df['volume_diff'].abs() / df['volume1']) * 100
    else:
        raise ValueError("Cannot compute MAPE")


def classify_roi(label: int) -> str:
    """Classify ROI as cortical or subcortical."""
    if label in CORTICAL_LABELS:
        return 'cortical'
    elif label in SUBCORTICAL_LABELS:
        return 'subcortical'
    else:
        return 'unknown'


def analyze_by_roi_type(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Compute summary statistics per ROI with type classification.
    """
    df = df.copy()
    df['mape'] = compute_mape(df)
    df['roi_type'] = df['label'].apply(classify_roi)

    # Compute mean volume per ROI
    df['mean_volume'] = (df['volume1'] + df['volume2']) / 2

    results = []
    for label in df['label'].unique():
        label_data = df[df['label'] == label]

        roi_type = classify_roi(label)
        label_name = CORTICAL_AND_SUBCORTICAL_NAMES.get(label, f"Label_{label}")

        mean_vol = label_data['mean_volume'].mean()

        results.append({
            'dataset': dataset_name,
            'label': label,
            'label_name': label_name,
            'roi_type': roi_type,
            'mean_volume_mm3': mean_vol,
            'mean_volume_ml': mean_vol / 1000,
            'n_pairs': len(label_data),
            'dice_median': label_data['dice'].median(),
            'dice_iqr': label_data['dice'].quantile(0.75) - label_data['dice'].quantile(0.25),
            'surface_dice_median': label_data['surface_dice'].median(),
            'hd95_median': label_data['hd95'].median(),
            'mape_median': label_data['mape'].median(),
        })

    return pd.DataFrame(results)


def compare_cortical_vs_subcortical(summary_df: pd.DataFrame) -> dict:
    """
    Statistical comparison of cortical vs subcortical stability.
    """
    cortical = summary_df[summary_df['roi_type'] == 'cortical']
    subcortical = summary_df[summary_df['roi_type'] == 'subcortical']

    if len(cortical) == 0 or len(subcortical) == 0:
        return {'error': 'Not enough data for comparison'}

    metrics = ['dice_median', 'surface_dice_median', 'hd95_median', 'mape_median']
    results = {}

    for metric in metrics:
        c_vals = cortical[metric].dropna().values
        s_vals = subcortical[metric].dropna().values

        if len(c_vals) < 2 or len(s_vals) < 2:
            continue

        stat, p = mannwhitneyu(c_vals, s_vals, alternative='two-sided')

        results[metric] = {
            'cortical_median': np.median(c_vals),
            'cortical_iqr': np.percentile(c_vals, 75) - np.percentile(c_vals, 25),
            'subcortical_median': np.median(s_vals),
            'subcortical_iqr': np.percentile(s_vals, 75) - np.percentile(s_vals, 25),
            'U_statistic': stat,
            'p_value': p,
            'better': 'subcortical' if (
                ('dice' in metric and np.median(s_vals) > np.median(c_vals)) or
                ('hd95' in metric and np.median(s_vals) < np.median(c_vals)) or
                ('mape' in metric and np.median(s_vals) < np.median(c_vals))
            ) else 'cortical'
        }

    return results


def correlate_with_volume(summary_df: pd.DataFrame) -> dict:
    """
    Correlate stability metrics with ROI volume.
    """
    results = {}

    metrics = ['dice_median', 'surface_dice_median', 'hd95_median', 'mape_median']

    for metric in metrics:
        valid = summary_df.dropna(subset=['mean_volume_mm3', metric])
        if len(valid) < 5:
            continue

        rho, p = spearmanr(valid['mean_volume_mm3'], valid[metric])

        results[metric] = {
            'spearman_r': rho,
            'p_value': p,
            'n': len(valid),
            'interpretation': 'larger ROIs more stable' if (
                ('dice' in metric and rho > 0) or
                ('hd95' in metric and rho < 0) or
                ('mape' in metric and rho < 0)
            ) else 'smaller ROIs more stable' if (
                ('dice' in metric and rho < 0) or
                ('hd95' in metric and rho > 0) or
                ('mape' in metric and rho > 0)
            ) else 'no clear pattern'
        }

    return results


def plot_volume_vs_stability(summary_df: pd.DataFrame, output_path: Path, dataset_name: str):
    """
    Create scatter plots of volume vs stability metrics.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    metrics = [
        ('dice_median', 'Dice Coefficient', False),
        ('surface_dice_median', 'Surface Dice', False),
        ('hd95_median', 'HD95 (mm)', True),
        ('mape_median', 'MAPE (%)', True)
    ]

    for ax, (metric, label, invert) in zip(axes.flat, metrics):
        valid = summary_df.dropna(subset=['mean_volume_ml', metric])

        # Color by ROI type
        colors = {'cortical': 'blue', 'subcortical': 'red', 'unknown': 'gray'}

        for roi_type in valid['roi_type'].unique():
            subset = valid[valid['roi_type'] == roi_type]
            ax.scatter(
                subset['mean_volume_ml'],
                subset[metric],
                c=colors.get(roi_type, 'gray'),
                label=roi_type.capitalize(),
                alpha=0.7,
                s=60
            )

        # Add correlation
        rho, p = spearmanr(valid['mean_volume_ml'], valid[metric])
        p_str = f"p < 0.001" if p < 0.001 else f"p = {p:.3f}"

        ax.set_xlabel('Mean Volume (mL)', fontsize=11)
        ax.set_ylabel(label, fontsize=11)
        ax.set_title(f'{label} vs Volume\n(Spearman r = {rho:.3f}, {p_str})', fontsize=10)
        ax.legend(loc='best', fontsize=9)

        # Add trend line
        z = np.polyfit(valid['mean_volume_ml'], valid[metric], 1)
        p_line = np.poly1d(z)
        x_line = np.linspace(valid['mean_volume_ml'].min(), valid['mean_volume_ml'].max(), 100)
        ax.plot(x_line, p_line(x_line), 'k--', alpha=0.5, linewidth=1.5)

    plt.suptitle(f'{dataset_name}: ROI Volume vs Stability', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved figure to {output_path}")


def plot_cortical_vs_subcortical(summary_df: pd.DataFrame, output_path: Path, dataset_name: str):
    """
    Box plots comparing cortical vs subcortical.
    """
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))

    metrics = [
        ('dice_median', 'Dice Coefficient'),
        ('surface_dice_median', 'Surface Dice'),
        ('hd95_median', 'HD95 (mm)'),
        ('mape_median', 'MAPE (%)')
    ]

    for ax, (metric, label) in zip(axes, metrics):
        valid = summary_df[summary_df['roi_type'].isin(['cortical', 'subcortical'])]

        sns.boxplot(data=valid, x='roi_type', y=metric, ax=ax,
                    order=['cortical', 'subcortical'],
                    palette={'cortical': 'steelblue', 'subcortical': 'indianred'})

        ax.set_xlabel('')
        ax.set_ylabel(label, fontsize=11)
        ax.set_xticklabels(['Cortical', 'Subcortical'], fontsize=10)

        # Add p-value
        cortical = valid[valid['roi_type'] == 'cortical'][metric].dropna()
        subcortical = valid[valid['roi_type'] == 'subcortical'][metric].dropna()

        if len(cortical) >= 2 and len(subcortical) >= 2:
            _, p = mannwhitneyu(cortical, subcortical, alternative='two-sided')
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
            y_max = valid[metric].max()
            ax.text(0.5, y_max * 1.05, sig, ha='center', fontsize=14, fontweight='bold')

    plt.suptitle(f'{dataset_name}: Cortical vs Subcortical Stability', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved figure to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze ROI stability by type and volume')
    parser.add_argument('--simon', type=str, default='data/consecutive_fs8_SIMON.csv',
                        help='Path to SIMON CSV')
    parser.add_argument('--srpbs', type=str, default='data/srpbs_freesurfer8_metrics.csv',
                        help='Path to SRPBS CSV (with all ROIs including subcortical)')
    parser.add_argument('--output-dir', type=str, default='outputs',
                        help='Output directory')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    (output_dir / 'tables').mkdir(parents=True, exist_ok=True)
    (output_dir / 'figures').mkdir(parents=True, exist_ok=True)

    # Load data
    print("Loading data...")
    simon_df = pd.read_csv(args.simon)
    print(f"SIMON: {len(simon_df)} rows, {simon_df['label'].nunique()} labels")

    srpbs_df = pd.read_csv(args.srpbs)
    print(f"SRPBS: {len(srpbs_df)} rows, {srpbs_df['label'].nunique()} labels")

    # Analyze by ROI type
    print("\n" + "="*60)
    print("ANALYZING ROI STABILITY BY TYPE AND SIZE")
    print("="*60)

    # SIMON analysis
    # SIMON = 1 subject, multiple scanners over years (cross-scanner + longitudinal aging)
    print("\n--- SIMON (cross-scanner, longitudinal) ---")
    simon_summary = analyze_by_roi_type(simon_df, 'SIMON')

    print("\nCortical vs Subcortical comparison:")
    simon_comparison = compare_cortical_vs_subcortical(simon_summary)
    for metric, result in simon_comparison.items():
        if isinstance(result, dict) and 'p_value' in result:
            print(f"  {metric}:")
            print(f"    Cortical: {result['cortical_median']:.3f} (IQR: {result['cortical_iqr']:.3f})")
            print(f"    Subcortical: {result['subcortical_median']:.3f} (IQR: {result['subcortical_iqr']:.3f})")
            print(f"    p = {result['p_value']:.4f}, Better: {result['better']}")

    print("\nCorrelation with ROI volume:")
    simon_vol_corr = correlate_with_volume(simon_summary)
    for metric, result in simon_vol_corr.items():
        print(f"  {metric}: r = {result['spearman_r']:.3f}, p = {result['p_value']:.4f}")
        print(f"    => {result['interpretation']}")

    # SRPBS analysis
    # SRPBS = travelling subjects, different 3T scanners on consecutive days (pure cross-scanner)
    print("\n--- SRPBS (cross-scanner, short-term) ---")
    srpbs_summary = analyze_by_roi_type(srpbs_df, 'SRPBS')

    print("\nCortical vs Subcortical comparison:")
    srpbs_comparison = compare_cortical_vs_subcortical(srpbs_summary)
    for metric, result in srpbs_comparison.items():
        if isinstance(result, dict) and 'p_value' in result:
            print(f"  {metric}:")
            print(f"    Cortical: {result['cortical_median']:.3f} (IQR: {result['cortical_iqr']:.3f})")
            print(f"    Subcortical: {result['subcortical_median']:.3f} (IQR: {result['subcortical_iqr']:.3f})")
            print(f"    p = {result['p_value']:.4f}, Better: {result['better']}")

    print("\nCorrelation with ROI volume:")
    srpbs_vol_corr = correlate_with_volume(srpbs_summary)
    for metric, result in srpbs_vol_corr.items():
        print(f"  {metric}: r = {result['spearman_r']:.3f}, p = {result['p_value']:.4f}")
        print(f"    => {result['interpretation']}")

    # Save summaries
    all_summary = pd.concat([simon_summary, srpbs_summary], ignore_index=True)
    all_summary.to_csv(output_dir / 'tables' / 'roi_stability_by_type.csv', index=False, float_format='%.4f')
    print(f"\nSaved summary to {output_dir / 'tables' / 'roi_stability_by_type.csv'}")

    # Create plots
    print("\nCreating plots...")
    plot_volume_vs_stability(simon_summary, output_dir / 'figures' / 'volume_vs_stability_simon.pdf', 'SIMON')
    plot_volume_vs_stability(srpbs_summary, output_dir / 'figures' / 'volume_vs_stability_srpbs.pdf', 'SRPBS')
    plot_cortical_vs_subcortical(simon_summary, output_dir / 'figures' / 'cortical_vs_subcortical_simon.pdf', 'SIMON')
    plot_cortical_vs_subcortical(srpbs_summary, output_dir / 'figures' / 'cortical_vs_subcortical_srpbs.pdf', 'SRPBS')

    # Print final summary
    print("\n" + "="*60)
    print("SUMMARY FOR REBUTTAL")
    print("="*60)

    print("\n1. CORTICAL VS SUBCORTICAL:")
    for dataset, comparison in [('SIMON', simon_comparison), ('SRPBS', srpbs_comparison)]:
        print(f"\n  {dataset}:")
        for metric in ['dice_median', 'hd95_median', 'mape_median']:
            if metric in comparison and isinstance(comparison[metric], dict):
                r = comparison[metric]
                sig = "*" if r['p_value'] < 0.05 else ""
                print(f"    {metric}: {r['better']} better{sig} (p={r['p_value']:.3f})")

    print("\n2. VOLUME DEPENDENCY:")
    for dataset, vol_corr in [('SIMON', simon_vol_corr), ('SRPBS', srpbs_vol_corr)]:
        print(f"\n  {dataset}:")
        for metric in ['dice_median', 'hd95_median', 'mape_median']:
            if metric in vol_corr:
                r = vol_corr[metric]
                sig = "*" if r['p_value'] < 0.05 else ""
                print(f"    {metric}: r={r['spearman_r']:.3f}{sig} => {r['interpretation']}")


if __name__ == '__main__':
    main()
