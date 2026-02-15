"""
ICC (Intraclass Correlation Coefficient) analysis for volume reproducibility.

Computes ICC(3,1) - two-way mixed effects, single measurement, consistency.
Used for test-retest reliability assessment of volume measurements.

Interpretation:
- < 0.50: Poor
- 0.50-0.75: Moderate
- 0.75-0.90: Good
- > 0.90: Excellent
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.regions import CORTICAL_AND_SUBCORTICAL_NAMES


def icc_3_1(measurements: np.ndarray) -> tuple:
    """
    Compute ICC(3,1) - two-way mixed effects, single measurement, consistency.

    Args:
        measurements: 2D array of shape (n_targets, n_raters)
                     Each row is a target (e.g., ROI for a session pair)
                     Each column is a rater/measurement occasion

    Returns:
        (icc, ci_lower, ci_upper) - ICC value and 95% CI
    """
    if measurements.ndim != 2:
        return np.nan, np.nan, np.nan

    n, k = measurements.shape  # n targets, k raters

    if n < 2 or k < 2:
        return np.nan, np.nan, np.nan

    # Grand mean
    grand_mean = np.mean(measurements)

    # Between-targets sum of squares
    target_means = np.mean(measurements, axis=1)
    SS_B = k * np.sum((target_means - grand_mean) ** 2)
    df_B = n - 1

    # Between-raters sum of squares (for mixed model)
    rater_means = np.mean(measurements, axis=0)
    SS_J = n * np.sum((rater_means - grand_mean) ** 2)
    df_J = k - 1

    # Total sum of squares
    SS_T = np.sum((measurements - grand_mean) ** 2)
    df_T = n * k - 1

    # Residual (error) sum of squares
    SS_E = SS_T - SS_B - SS_J
    df_E = (n - 1) * (k - 1)

    # Mean squares
    MS_B = SS_B / df_B if df_B > 0 else 0
    MS_E = SS_E / df_E if df_E > 0 else 0

    # ICC(3,1) - single measurement, consistency
    if MS_B + (k - 1) * MS_E == 0:
        return np.nan, np.nan, np.nan

    icc = (MS_B - MS_E) / (MS_B + (k - 1) * MS_E)

    # 95% CI using F-distribution approximation
    from scipy.stats import f as f_dist

    if MS_E == 0:
        return icc, np.nan, np.nan

    F_value = MS_B / MS_E

    # Lower bound
    F_L = F_value / f_dist.ppf(0.975, df_B, df_E)
    ci_lower = (F_L - 1) / (F_L + k - 1)

    # Upper bound
    F_U = F_value / f_dist.ppf(0.025, df_B, df_E)
    ci_upper = (F_U - 1) / (F_U + k - 1)

    return icc, ci_lower, ci_upper


def interpret_icc(icc: float) -> str:
    """Interpret ICC value according to Koo & Li (2016) guidelines."""
    if np.isnan(icc):
        return "N/A"
    elif icc < 0.50:
        return "poor"
    elif icc < 0.75:
        return "moderate"
    elif icc < 0.90:
        return "good"
    else:
        return "excellent"


def prepare_volume_data_for_icc(df: pd.DataFrame, label: int) -> np.ndarray:
    """
    Prepare volume data for ICC computation from pairwise data.

    For a single ROI, extracts all unique volume measurements across sessions
    and reshapes for ICC computation.

    Args:
        df: DataFrame with session1, session2, volume1, volume2 columns
        label: ROI label to filter

    Returns:
        2D array suitable for ICC computation
    """
    label_df = df[df['label'] == label].copy()

    if len(label_df) == 0:
        return np.array([]).reshape(0, 0)

    # Extract all unique session-volume pairs
    vol1_data = label_df[['session1', 'volume1']].rename(
        columns={'session1': 'session', 'volume1': 'volume'})
    vol2_data = label_df[['session2', 'volume2']].rename(
        columns={'session2': 'session', 'volume2': 'volume'})

    all_vols = pd.concat([vol1_data, vol2_data]).drop_duplicates()

    # Get unique sessions
    sessions = all_vols['session'].unique()

    if len(sessions) < 2:
        return np.array([]).reshape(0, 0)

    # For ICC, we need repeated measurements
    # Treat each session as a "rater" measuring the same ROI
    # This gives us n=1 target (the ROI) with k raters (sessions)
    # However, this is not the typical ICC setup

    # Alternative: Use pairs as repeated measurements
    # Each pair is a "measurement occasion"
    # For single ROI: volume1 and volume2 are two measurements of the same target

    # Extract volume pairs
    volumes = label_df[['volume1', 'volume2']].values

    return volumes


def compute_icc_for_dataset(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Compute ICC for all ROIs in a dataset.

    Args:
        df: DataFrame with pairwise volume data
        dataset_name: Name of the dataset

    Returns:
        DataFrame with ICC results per ROI
    """
    results = []
    labels = df['label'].unique()

    for label in labels:
        label_name = CORTICAL_AND_SUBCORTICAL_NAMES.get(label, f"Label_{label}")

        volumes = prepare_volume_data_for_icc(df, label)

        if volumes.size == 0 or volumes.shape[0] < 3:
            continue

        icc, ci_lower, ci_upper = icc_3_1(volumes)

        results.append({
            'dataset': dataset_name,
            'label': label,
            'label_name': label_name,
            'icc': icc,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_pairs': volumes.shape[0],
            'interpretation': interpret_icc(icc)
        })

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description='Compute ICC for volume reproducibility')
    parser.add_argument('--simon', type=str, default='data/consecutive_fs8_SIMON.csv',
                        help='Path to SIMON (within-scanner) CSV')
    parser.add_argument('--srpbs', type=str, default='data/cortical_all_sub_session_metrics.csv',
                        help='Path to SRPBS (cross-scanner) CSV')
    parser.add_argument('--output', type=str, default='outputs/tables/icc_volumes.csv',
                        help='Output CSV path')
    args = parser.parse_args()

    # Load datasets
    print(f"Loading SIMON data from {args.simon}...")
    simon_df = pd.read_csv(args.simon)
    print(f"  Loaded {len(simon_df)} rows, {simon_df['label'].nunique()} unique labels")

    print(f"Loading SRPBS data from {args.srpbs}...")
    srpbs_df = pd.read_csv(args.srpbs)
    print(f"  Loaded {len(srpbs_df)} rows, {srpbs_df['label'].nunique()} unique labels")

    # Compute ICC
    print("\nComputing ICC for SIMON (within-scanner)...")
    simon_results = compute_icc_for_dataset(simon_df, 'SIMON')

    print("Computing ICC for SRPBS (cross-scanner)...")
    srpbs_results = compute_icc_for_dataset(srpbs_df, 'SRPBS')

    # Combine results
    all_results = pd.concat([simon_results, srpbs_results], ignore_index=True)

    # Sort by label_name, dataset
    all_results = all_results.sort_values(['label_name', 'dataset'])

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_results.to_csv(output_path, index=False, float_format='%.4f')

    print(f"\nSaved {len(all_results)} rows to {output_path}")

    # Print summary
    print("\n=== ICC Summary ===")
    for dataset in all_results['dataset'].unique():
        ds_data = all_results[all_results['dataset'] == dataset]
        print(f"\n{dataset}:")
        print(f"  Mean ICC: {ds_data['icc'].mean():.3f}")
        print(f"  Median ICC: {ds_data['icc'].median():.3f}")
        print(f"  Range: [{ds_data['icc'].min():.3f} - {ds_data['icc'].max():.3f}]")

        print("  Interpretation distribution:")
        for interp in ['excellent', 'good', 'moderate', 'poor']:
            count = len(ds_data[ds_data['interpretation'] == interp])
            if count > 0:
                print(f"    {interp}: {count}")


if __name__ == '__main__':
    main()
