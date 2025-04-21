import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sns.set_style('whitegrid')
sns.set_context('paper')

FIGSIZE = (16, 8)
DPI = 70

simon_df = pd.read_csv('../../data/consecutive_fs8_SIMON.csv', index_col=0)
srpbs_ts_df = pd.read_csv('../../data/cortical_all_sub_session_metrics.csv', index_col=0)

simon_df['dataset'] = 'SIMON'
srpbs_ts_df['dataset'] = 'SRPBS_TS'

df = pd.concat([simon_df, srpbs_ts_df], axis=0)

# separating left and right hemisphere
df_left = df[df['label_name'].str.contains(' L', case=True)]
df_right = df[df['label_name'].str.contains(' R', case=True)]

# removing L and R from labels
df_left.loc[:, 'label_name'] = df_left['label_name'].str.replace(' L', '', case=True)
df_right.loc[:, 'label_name'] = df_right['label_name'].str.replace(' R', '', case=True)

# df_left_melted = pd.melt(df_left, id_vars=["label_name"],
#                          value_vars=["percentage_vol_diff"],
#                          var_name="dataset", value_name="percentage_vol_diff")
#
# df_right_melted = pd.melt(df_right, id_vars=["label_name"],
#                           value_vars=["percentage_vol_diff"],
#                           var_name="dataset", value_name="percentage_vol_diff")

df_left_melted = df_left
df_right_melted = df_right


fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=FIGSIZE, sharex=True)

flierprops = dict(marker="o", markerfacecolor="white", markersize=6, markeredgecolor="k")

# left structures
sns.boxplot(
    data=df_left_melted,
    x="percentage_vol_diff",
    y="label_name",
    hue="dataset",
    palette={"SIMON": "0.6", "SRPBS_TS": "white"},
    linecolor="black",
    linewidth=1.3,
    width=0.6,
    flierprops=flierprops,
    ax=ax1, legend=False
)

ax1.set_title("Left Hemisphere", pad=12)
ax1.set_xlabel("Volume Difference (%)", labelpad=10)
ax1.set_ylabel("")

# right structures
sns.boxplot(
    data=df_right_melted,
    x="percentage_vol_diff",
    y="label_name",
    hue="dataset",
    palette={"SIMON": "0.6", "SRPBS_TS": "white"},
    linecolor="black",
    linewidth=1.3,
    width=0.6,
    flierprops=flierprops,
    ax=ax2, legend=False
)
ax2.set_title("Right Hemisphere", pad=12)
ax2.set_xlabel("Volume Difference (%)", labelpad=10)
ax2.set_ylabel("")

# legend
handles = [Patch(facecolor='0.6', edgecolor='black', label='SIMON'),
           Patch(facecolor='white', edgecolor='black', label='SRPBS_TS')]
fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.95, 0.05), ncol=2, frameon=False)

plt.suptitle("Percentage difference from sector-specific mean in SIMON and SRPBS_TS datasets", y=1.02)
sns.despine()
plt.tight_layout()
plt.savefig(f"simon_srpbs_ts_comparison.pdf", bbox_inches='tight', transparent=False, dpi=DPI)
