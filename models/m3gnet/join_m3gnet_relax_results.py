# %%
from __future__ import annotations

import os
from datetime import datetime
from glob import glob

import pandas as pd
from pymatgen.analysis.phase_diagram import PDEntry
from pymatgen.core import Structure
from tqdm import tqdm

from matbench_discovery import ROOT, as_dict_handler
from matbench_discovery.energy import get_e_form_per_atom

__author__ = "Janosh Riebesell"
__date__ = "2022-08-16"

today = f"{datetime.now():%Y-%m-%d}"


# %%
module_dir = os.path.dirname(__file__)
task_type = "IS2RE"
date = "2022-10-31"
glob_pattern = f"{date}-m3gnet-wbm-{task_type}/*.json.gz"
file_paths = sorted(glob(f"{module_dir}/{glob_pattern}"))
print(f"Found {len(file_paths):,} files for {glob_pattern = }")

dfs: dict[str, pd.DataFrame] = {}


# %%
# 2022-08-16 tried multiprocessing.Pool() to load files in parallel but was somehow
# slower than serial loading
for file_path in tqdm(file_paths):
    if file_path in dfs:
        continue
    try:
        # keep whole dataframe in memory
        df = pd.read_json(file_path).set_index("material_id")
        df.index.name = "material_id"
        col_map = dict(
            final_structure="m3gnet_structure", trajectory="m3gnet_trajectory"
        )
        df = df.rename(columns=col_map)
        df.reset_index().to_json(file_path)
        df[f"m3gnet_energy_{task_type}"] = df.m3gnet_trajectory.map(
            lambda x: x["energies"][-1][0]
        )
        df["m3gnet_structure"] = df.m3gnet_structure.map(Structure.from_dict)
        df["formula"] = df.m3gnet_structure.map(lambda x: x.alphabetical_formula)
        df["m3gnet_volume"] = df.m3gnet_structure.map(lambda x: x.volume)
        df["n_sites"] = df.m3gnet_structure.map(len)
        # drop trajectory to save memory
        dfs[file_path] = df.drop(columns=["m3gnet_trajectory"])
    except FileNotFoundError:
        continue


# %%
df_m3gnet = pd.concat(dfs.values())


# %%
df_m3gnet["e_form_per_atom_m3gnet"] = [
    get_e_form_per_atom(PDEntry(row.m3gnet_structure.composition, row.m3gnet_energy))
    for row in tqdm(df_m3gnet.itertuples(), total=len(df_m3gnet), disable=None)
]
df_m3gnet.isna().sum()


# %%
out_path = f"{ROOT}/models/m3gnet/{today}-m3gnet-wbm-{task_type}.json.gz"
df_m3gnet.reset_index().to_json(out_path, default_handler=as_dict_handler)

# out_path = f"{ROOT}/models/m3gnet/2022-08-16-m3gnet-wbm-IS2RE.json.gz"
# df_m3gnet = pd.read_json(out_path).set_index("material_id")