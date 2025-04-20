from pathlib import Path

import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sns.set_style('whitegrid')
sns.set_context('paper')

FIGSIZE = (16, 8)
DPI = 70

data_folder = Path('../../data/')

for csv_file in data_folder.glob('*.csv'):
    df = pd.read_csv(csv_file, index_col=0)

    # separating left and right hemisphere
    df_left = df[df['label_name'].str.contains(' L', case=True)]
    df_right = df[df['label_name'].str.contains(' R', case=True)]

    # removing L and R from labels
    df_left.loc[:, 'label_name'] = df_left['label_name'].str.replace(' L', '', case=True)
    df_right.loc[:, 'label_name'] = df_right['label_name'].str.replace(' R', '', case=True)

    # first plot
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=FIGSIZE, sharex=True, sharey=False)
    # common configuration
    flierprops = dict(marker="o", markerfacecolor="white", markersize=6, markeredgecolor="k")
    # left structures
    sns.boxplot(
        data=df_left,
        x="percentage_vol_diff",
        y="label_name",
        color="white",
        linecolor="black",
        linewidth=1.3,
        width=0.6,
        flierprops=flierprops,
        ax=ax1
    )
    ax1.set_title("Left Hemisphere Structures", pad=15)
    ax1.set_xlabel("Volume Difference (%)", labelpad=10)
    ax1.set_ylabel("")

    # right structures
    sns.boxplot(
        data=df_right,
        x="percentage_vol_diff",
        y="label_name",
        color="white",
        linecolor="black",
        linewidth=1.3,
        width=0.6,
        flierprops=flierprops,
        ax=ax2
    )
    ax2.set_title("Right Hemisphere Structures", pad=15)
    ax2.set_xlabel("Volume Difference (%)", labelpad=10)
    ax2.set_ylabel("")

    plt.suptitle("Inter-Scanner Variability in Brain Volumes by Hemisphere", y=1.02)
    plt.xlim(df['percentage_vol_diff'].min() * 1.1,
             df['percentage_vol_diff'].max() * 1.1)
    sns.despine()
    plt.tight_layout()

    fig.text(0.5, -0.05, "Percentage difference from sector-specific mean",
             ha="center", fontsize=12)

    plt.savefig(f"{csv_file.stem}_percentage_vol_diff.png", bbox_inches='tight', transparent=False, dpi=DPI)

    # second plot
    df_left_melted = pd.melt(df_left, id_vars=["label_name"],
                             value_vars=["dice", "surface_dice"],
                             var_name="metric", value_name="value")

    df_right_melted = pd.melt(df_right, id_vars=["label_name"],
                              value_vars=["dice", "surface_dice"],
                              var_name="metric", value_name="value")

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=FIGSIZE, sharex=True)

    # left structures
    sns.boxplot(
        data=df_left_melted,
        x="value",
        y="label_name",
        hue="metric",
        palette={"dice": "0.6", "surface_dice": "white"},
        linecolor="black",
        linewidth=1.3,
        width=0.6,
        flierprops=flierprops,
        ax=ax1, legend=False
    )

    ax1.set_title("Left Hemisphere", pad=12)
    ax1.set_xlabel("Metric Value", labelpad=10)
    ax1.set_ylabel("")

    # right structures
    sns.boxplot(
        data=df_right_melted,
        x="value",
        y="label_name",
        hue="metric",
        palette={"dice": "0.6", "surface_dice": "white"},
        linecolor="black",
        linewidth=1.3,
        width=0.6,
        flierprops=flierprops,
        ax=ax2, legend=False
    )
    ax2.set_title("Right Hemisphere", pad=12)
    ax2.set_xlabel("Metric Value", labelpad=10)
    ax2.set_ylabel("")

    # legend
    handles = [Patch(facecolor='0.6', edgecolor='black', label='Dice'),
               Patch(facecolor='white', edgecolor='black', label='Surface Dice')]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.95, 0.05), ncol=2, frameon=False)

    plt.suptitle("Dice vs Surface Dice Metrics by Hemisphere", y=1.02)
    sns.despine()
    plt.tight_layout()
    plt.savefig(f"{csv_file.stem}_dice_surface_dice.png", bbox_inches='tight', transparent=False, dpi=DPI)
