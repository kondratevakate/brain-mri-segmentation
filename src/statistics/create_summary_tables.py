"""
Create publication-ready summary tables combining all statistical analyses.

Generates tables with:
- Median [IQR] for each metric
- 95% Bootstrap CI
- Within-scanner vs cross-scanner comparison
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.regions import CORTICAL_AND_SUBCORTICAL_NAMES


def compute_mape(df: pd.DataFrame) -> pd.Series:
    """Compute MAPE for volume."""
    if 'percentage_vol_diff' in df.columns:
        return df['percentage_vol_diff'].abs() * 100
    elif 'volume_diff' in df.columns and 'volume1' in df.columns:
        return (df['volume_diff'].abs() / df['volume1']) * 100
    else:
        raise ValueError("Cannot compute MAPE")


def format_median_iqr(values: pd.Series, decimals: int = 3) -> str:
    """Format as 'median [Q1-Q3]'."""
    if len(values) == 0:
        return "N/A"
    median = values.median()
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    return f"{median:.{decimals}f} [{q1:.{decimals}f}-{q3:.{decimals}f}]"


def format_ci(row: pd.Series, value_col: str, ci_low_col: str, ci_high_col: str,
              decimals: int = 3) -> str:
    """Format as 'value [CI_low-CI_high]'."""
    value = row[value_col]
    ci_low = row[ci_low_col]
    ci_high = row[ci_high_col]
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f} [{ci_low:.{decimals}f}-{ci_high:.{decimals}f}]"


def create_roi_summary(simon_df: pd.DataFrame, srpbs_df: pd.DataFrame,
                       bootstrap_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Create summary table with median [IQR] per ROI per dataset.

    Args:
        simon_df: SIMON raw data
        srpbs_df: SRPBS raw data
        bootstrap_df: Bootstrap CI results (optional)

    Returns:
        Summary DataFrame
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

    for label in sorted(common_labels):
        label_name = CORTICAL_AND_SUBCORTICAL_NAMES.get(label, f"Label_{label}")

        simon_label = simon_df[simon_df['label'] == label]
        srpbs_label = srpbs_df[srpbs_df['label'] == label]

        row = {
            'label': label,
            'label_name': label_name,
            'n_within': len(simon_label),
            'n_cross': len(srpbs_label)
        }

        for metric in metrics:
            if metric in simon_label.columns:
                row[f'{metric}_within'] = format_median_iqr(simon_label[metric].dropna())
            if metric in srpbs_label.columns:
                row[f'{metric}_cross'] = format_median_iqr(srpbs_label[metric].dropna())

        results.append(row)

    return pd.DataFrame(results)


def create_condensed_summary(simon_df: pd.DataFrame, srpbs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create condensed summary showing overall statistics per ROI.
    """
    simon_df = simon_df.copy()
    srpbs_df = srpbs_df.copy()
    simon_df['mape'] = compute_mape(simon_df)
    srpbs_df['mape'] = compute_mape(srpbs_df)

    results = []
    common_labels = set(simon_df['label'].unique()) & set(srpbs_df['label'].unique())

    for label in sorted(common_labels):
        label_name = CORTICAL_AND_SUBCORTICAL_NAMES.get(label, f"Label_{label}")

        simon_label = simon_df[simon_df['label'] == label]
        srpbs_label = srpbs_df[srpbs_df['label'] == label]

        row = {
            'ROI': label_name,
            'n (within)': len(simon_label),
            'n (cross)': len(srpbs_label),
            'Dice (within)': format_median_iqr(simon_label['dice'].dropna(), 2),
            'Dice (cross)': format_median_iqr(srpbs_label['dice'].dropna(), 2),
            'HD95 (within)': format_median_iqr(simon_label['hd95'].dropna(), 1),
            'HD95 (cross)': format_median_iqr(srpbs_label['hd95'].dropna(), 1),
            'MAPE% (within)': format_median_iqr(simon_label['mape'].dropna(), 1),
            'MAPE% (cross)': format_median_iqr(srpbs_label['mape'].dropna(), 1),
        }
        results.append(row)

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description='Create summary tables')
    parser.add_argument('--simon', type=str, default='data/consecutive_fs8_SIMON.csv',
                        help='Path to SIMON CSV')
    parser.add_argument('--srpbs', type=str, default='data/cortical_all_sub_session_metrics.csv',
                        help='Path to SRPBS CSV')
    parser.add_argument('--bootstrap', type=str, default='outputs/tables/bootstrap_ci_summary.csv',
                        help='Path to bootstrap CI CSV')
    parser.add_argument('--output-dir', type=str, default='outputs/tables',
                        help='Output directory')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("Loading data...")
    simon_df = pd.read_csv(args.simon)
    srpbs_df = pd.read_csv(args.srpbs)

    # Load bootstrap results if available
    bootstrap_df = None
    if Path(args.bootstrap).exists():
        bootstrap_df = pd.read_csv(args.bootstrap)
        print(f"Loaded bootstrap CI from {args.bootstrap}")

    # Create full summary
    print("Creating full summary table...")
    full_summary = create_roi_summary(simon_df, srpbs_df, bootstrap_df)
    full_path = output_dir / 'summary_full.csv'
    full_summary.to_csv(full_path, index=False)
    print(f"Saved to {full_path}")

    # Create condensed summary
    print("Creating condensed summary table...")
    condensed = create_condensed_summary(simon_df, srpbs_df)
    condensed_path = output_dir / 'summary_condensed.csv'
    condensed.to_csv(condensed_path, index=False)
    print(f"Saved to {condensed_path}")

    # Print preview
    print("\n=== Condensed Summary Preview ===")
    print(condensed.to_string(index=False))


if __name__ == '__main__':
    main()
