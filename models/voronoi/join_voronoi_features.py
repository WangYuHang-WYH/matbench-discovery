# %%
from __future__ import annotations

import os
from glob import glob

import pandas as pd
from tqdm import tqdm

__author__ = "Janosh Riebesell"
__date__ = "2022-08-16"


# %%
module_dir = os.path.dirname(__file__)
date, data = "2022-11-25", "mp"
glob_pattern = f"{date}-features-{data}/voronoi-features-{data}-*.csv.bz2"
file_paths = sorted(glob(f"{module_dir}/{glob_pattern}"))
print(f"Found {len(file_paths):,} files for {glob_pattern = }")

dfs: dict[str, pd.DataFrame] = {}


# %%
for file_path in tqdm(file_paths):
    if file_path in dfs:
        continue
    df = pd.read_csv(file_path).set_index("material_id")
    dfs[file_path] = df


# %%
df_features = pd.concat(dfs.values()).round(4)

ax = df_features.isna().sum().value_counts().T.plot.bar()
ax.set(xlabel="# NaNs", ylabel="# columns", title="NaNs per column")


# %%
out_path = f"{module_dir}/{date}-features-{data}.csv.bz2"
df_features.to_csv(out_path)