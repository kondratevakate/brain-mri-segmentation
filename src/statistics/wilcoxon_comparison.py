"""
Wilcoxon rank-sum test comparing within-scanner vs cross-scanner variability.

For each ROI and metric:
- Mann-Whitney U test (= Wilcoxon rank-sum for unpaired samples)
- Cliff's delta effect size
- FDR correction (Benjamini-Hochberg)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.regions import CORTICAL_AND_SUBCORTICAL_NAMES


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute Cliff's delta effect size.

    Interpretation:
    - |d| < 0.147: negligible
    - |d| < 0.33: small
    - |d| < 0.474: medium
    - |d| >= 0.474: large

    Args:
        x: First group values
        y: Second group values

    Returns:
        Cliff's delta in range [-1, 1]
    """
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return np.nan

    # Count dominance
    dominance = 0
    for xi in x:
        for yj in y:
            if xi > yj:
                dominance += 1
            elif xi < yj:
                dominance -= 1

    return dominance / (n1 * n2)


def interpret_cliffs_delta(d: float) -> str:
    """Interpret Cliff's delta magnitude."""
    if np.isnan(d):
        return "N/A"
    abs_d = abs(d)
    if abs_d < 0.147:
        return "negligible"
    elif abs_d < 0.33:
        return "small"
    elif abs_d < 0.474:
        return "medium"
    else:
        return "large"


def fdr_correction(p_values: np.ndarray, alpha: float = 0.05) -> tuple:
    """
    Benjamini-Hochberg FDR correction.

    Args:
        p_values: Array of p-values
        alpha: Significance level

    Returns:
        (p_adjusted, significant)
    """
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])

    # Handle NaN values
    valid_mask = ~np.isnan(p_values)
    p_valid = p_values[valid_mask]

    if len(p_valid) == 0:
        return np.full(n, np.nan), np.full(n, False)

    # Sort p-values
    sorted_idx = np.argsort(p_valid)
    sorted_p = p_valid[sorted_idx]

    # Compute adjusted p-values
    m = len(p_valid)
    adjusted = np.zeros(m)
    for i in range(m - 1, -1, -1):
        if i == m - 1:
            adjusted[i] = sorted_p[i]
        else:
            adjusted[i] = min(adjusted[i + 1], sorted_p[i] * m / (i + 1))

    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)

    # Unsort
    unsorted_adjusted = np.zeros(m)
    unsorted_adjusted[sorted_idx] = adjusted

    # Fill result arrays
    p_adjusted = np.full(n, np.nan)
    p_adjusted[valid_mask] = unsorted_adjusted

    significant = p_adjusted < alpha

    return p_adjusted, significant


def compute_mape(df: pd.DataFrame) -> pd.Series:
    """Compute MAPE (Mean Absolute Percentage Error) for volume."""
    if 'percentage_vol_diff' in df.columns:
        return df['percentage_vol_diff'].abs() * 100
    elif 'volume_diff' in df.columns and 'volume1' in df.columns:
        return (df['volume_diff'].abs() / df['volume1']) * 100
    else:
        raise ValueError("Cannot compute MAPE: missing required columns")


def compare_datasets(simon_df: pd.DataFrame, srpbs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare within-scanner (SIMON) vs cross-scanner (SRPBS) for all ROIs and metrics.

    Args:
        simon_df: SIMON dataset (within-scanner)
        srpbs_df: SRPBS dataset (cross-scanner)

    Returns:
        DataFrame with comparison results
    """
    # Ensure MAPE column exists
    simon_df = simon_df.copy()
    srpbs_df = srpbs_df.copy()
    simon_df['mape'] = compute_mape(simon_df)
    srpbs_df['mape'] = compute_mape(srpbs_df)

    metrics = ['dice', 'surface_dice', 'hd95', 'mape']
    results = []

    # Find common labels
    common_labels = set(simon_df['label'].unique()) & set(srpbs_df['label'].unique())
    print(f"Found {len(common_labels)} common labels")

    for label in sorted(common_labels):
        simon_label = simon_df[simon_df['label'] == label]
        srpbs_label = srpbs_df[srpbs_df['label'] == label]
        label_name = CORTICAL_AND_SUBCORTICAL_NAMES.get(label, f"Label_{label}")

        for metric in metrics:
            if metric not in simon_label.columns or metric not in srpbs_label.columns:
                continue

            x = simon_label[metric].dropna().values
            y = srpbs_label[metric].dropna().values

            if len(x) < 3 or len(y) < 3:
                continue

            # Mann-Whitney U test
            try:
                stat, p_value = mannwhitneyu(x, y, alternative='two-sided')
            except ValueError:
                stat, p_value = np.nan, np.nan

            # Cliff's delta
            delta = cliffs_delta(x, y)

            results.append({
                'label': label,
                'label_name': label_name,
                'metric': metric,
                'n_within': len(x),
                'n_cross': len(y),
                'median_within': np.median(x),
                'median_cross': np.median(y),
                'iqr_within': np.percentile(x, 75) - np.percentile(x, 25),
                'iqr_cross': np.percentile(y, 75) - np.percentile(y, 25),
                'U_statistic': stat,
                'p_value': p_value,
                'cliffs_delta': delta,
                'effect_size': interpret_cliffs_delta(delta)
            })

    results_df = pd.DataFrame(results)

    # FDR correction
    if len(results_df) > 0:
        p_adjusted, significant = fdr_correction(results_df['p_value'].values)
        results_df['p_adjusted'] = p_adjusted
        results_df['significant'] = significant

    return results_df


def main():
    parser = argparse.ArgumentParser(
        description='Wilcoxon rank-sum test: within-scanner vs cross-scanner')
    parser.add_argument('--simon', type=str, default='data/simon_freesurfer.csv',
                        help='Path to SIMON (within-scanner) CSV')
    parser.add_argument('--srpbs', type=str, default='data/cortical_all_sub_session_metrics.csv',
                        help='Path to SRPBS (cross-scanner) CSV')
    parser.add_argument('--output', type=str, default='outputs/tables/wilcoxon_within_vs_cross.csv',
                        help='Output CSV path')
    args = parser.parse_args()

    # Load datasets
    print(f"Loading SIMON data from {args.simon}...")
    simon_df = pd.read_csv(args.simon)
    print(f"  Loaded {len(simon_df)} rows, {simon_df['label'].nunique()} unique labels")

    print(f"Loading SRPBS data from {args.srpbs}...")
    srpbs_df = pd.read_csv(args.srpbs)
    print(f"  Loaded {len(srpbs_df)} rows, {srpbs_df['label'].nunique()} unique labels")

    # Compare
    print("\nComparing within-scanner vs cross-scanner...")
    results = compare_datasets(simon_df, srpbs_df)

    # Sort by label_name, metric
    results = results.sort_values(['label_name', 'metric'])

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False, float_format='%.4f')

    print(f"\nSaved {len(results)} comparisons to {output_path}")

    # Print summary
    print("\n=== Summary ===")
    significant = results[results['significant'] == True]
    print(f"Significant comparisons (FDR < 0.05): {len(significant)} / {len(results)}")

    print("\nEffect sizes distribution:")
    for effect in ['negligible', 'small', 'medium', 'large']:
        count = len(results[results['effect_size'] == effect])
        print(f"  {effect}: {count}")

    print("\nBy metric:")
    for metric in results['metric'].unique():
        metric_data = results[results['metric'] == metric]
        sig_count = len(metric_data[metric_data['significant'] == True])
        print(f"  {metric}: {sig_count}/{len(metric_data)} significant")


if __name__ == '__main__':
    main()
