"""
Bootstrap 95% confidence intervals for segmentation metrics.

Computes median and 95% CI (percentile method) for:
- Dice coefficient
- Surface Dice
- HD95 (Hausdorff Distance 95th percentile)
- MAPE (Mean Absolute Percentage Error of volume)

For each ROI, separately for within-scanner (SIMON) and cross-scanner (SRPBS) datasets.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.regions import CORTICAL_AND_SUBCORTICAL_NAMES


def bootstrap_ci(data: np.ndarray, B: int = 2000, alpha: float = 0.05) -> tuple:
    """
    Compute bootstrap confidence interval using percentile method.

    Args:
        data: 1D array of metric values
        B: Number of bootstrap resamples
        alpha: Significance level (0.05 for 95% CI)

    Returns:
        (median, ci_lower, ci_upper)
    """
    if len(data) < 2:
        return np.nan, np.nan, np.nan

    data = np.array(data)
    data = data[~np.isnan(data)]

    if len(data) < 2:
        return np.nan, np.nan, np.nan

    n = len(data)
    rng = np.random.default_rng(42)  # Reproducibility

    boot_medians = np.array([
        np.median(rng.choice(data, size=n, replace=True))
        for _ in range(B)
    ])

    return (
        np.median(data),
        np.percentile(boot_medians, 100 * alpha / 2),
        np.percentile(boot_medians, 100 * (1 - alpha / 2))
    )


def compute_mape(df: pd.DataFrame) -> pd.Series:
    """Compute MAPE (Mean Absolute Percentage Error) for volume."""
    if 'percentage_vol_diff' in df.columns:
        return df['percentage_vol_diff'].abs() * 100
    elif 'volume_diff' in df.columns and 'volume1' in df.columns:
        return (df['volume_diff'].abs() / df['volume1']) * 100
    else:
        raise ValueError("Cannot compute MAPE: missing required columns")


def process_dataset(df: pd.DataFrame, dataset_name: str, B: int = 2000) -> pd.DataFrame:
    """
    Compute bootstrap CI for all metrics and ROIs in a dataset.

    Args:
        df: DataFrame with columns: label, dice, surface_dice, hd95, and volume data
        dataset_name: Name identifier for the dataset (e.g., 'SIMON', 'SRPBS')
        B: Number of bootstrap resamples

    Returns:
        DataFrame with columns: dataset, label, label_name, metric, median, ci_lower, ci_upper, n
    """
    # Ensure MAPE column exists
    df = df.copy()
    df['mape'] = compute_mape(df)

    metrics = ['dice', 'surface_dice', 'hd95', 'mape']
    results = []

    # Get unique labels
    labels = df['label'].unique()

    for label in labels:
        label_data = df[df['label'] == label]
        label_name = CORTICAL_AND_SUBCORTICAL_NAMES.get(label, f"Label_{label}")

        for metric in metrics:
            if metric not in label_data.columns:
                continue

            values = label_data[metric].dropna().values

            if len(values) < 2:
                continue

            median, ci_lower, ci_upper = bootstrap_ci(values, B=B)

            results.append({
                'dataset': dataset_name,
                'label': label,
                'label_name': label_name,
                'metric': metric,
                'median': median,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'n': len(values)
            })

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description='Compute bootstrap 95% CI for segmentation metrics')
    parser.add_argument('--simon', type=str, default='data/consecutive_fs8_SIMON.csv',
                        help='Path to SIMON (within-scanner) CSV')
    parser.add_argument('--srpbs', type=str, default='data/cortical_all_sub_session_metrics.csv',
                        help='Path to SRPBS (cross-scanner) CSV')
    parser.add_argument('--output', type=str, default='outputs/tables/bootstrap_ci_summary.csv',
                        help='Output CSV path')
    parser.add_argument('--bootstrap-samples', type=int, default=2000,
                        help='Number of bootstrap samples')
    args = parser.parse_args()

    # Load datasets
    print(f"Loading SIMON data from {args.simon}...")
    simon_df = pd.read_csv(args.simon)
    print(f"  Loaded {len(simon_df)} rows, {simon_df['label'].nunique()} unique labels")

    print(f"Loading SRPBS data from {args.srpbs}...")
    srpbs_df = pd.read_csv(args.srpbs)
    print(f"  Loaded {len(srpbs_df)} rows, {srpbs_df['label'].nunique()} unique labels")

    # Process datasets
    print(f"\nComputing bootstrap CI with B={args.bootstrap_samples}...")

    print("Processing SIMON (within-scanner)...")
    simon_results = process_dataset(simon_df, 'SIMON', B=args.bootstrap_samples)

    print("Processing SRPBS (cross-scanner)...")
    srpbs_results = process_dataset(srpbs_df, 'SRPBS', B=args.bootstrap_samples)

    # Combine results
    all_results = pd.concat([simon_results, srpbs_results], ignore_index=True)

    # Sort by label_name, metric, dataset
    all_results = all_results.sort_values(['label_name', 'metric', 'dataset'])

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_results.to_csv(output_path, index=False, float_format='%.4f')

    print(f"\nSaved {len(all_results)} rows to {output_path}")

    # Print summary
    print("\n=== Summary ===")
    for dataset in all_results['dataset'].unique():
        ds_data = all_results[all_results['dataset'] == dataset]
        print(f"\n{dataset}:")
        for metric in ds_data['metric'].unique():
            metric_data = ds_data[ds_data['metric'] == metric]
            print(f"  {metric}: {len(metric_data)} ROIs, "
                  f"median range [{metric_data['median'].min():.3f} - {metric_data['median'].max():.3f}]")


if __name__ == '__main__':
    main()
