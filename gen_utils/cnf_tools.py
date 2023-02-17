# --------------------------------------------------------------------------- #
# Filename: cnf_tools.py
# Path: /cnf_tools.py
# Created Date: Sunday, January 15th 2023, 4:38:11 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Generic functions to deal with RESTORE configuration files."""
from typing import Any

import pandas as pd
import numpy as np

from data.zenodo_to_cnf import CNF_INDEX


def get_flow_element_dict(io_df: pd.DataFrame, by_element=False) -> dict[str, list]:
    """Create a dictionary with the flows as keys, and the connected processes as the item (in list).

    Args:
        io_df (pd.DataFrame): In/out dataframe from the configuration file. Must not have multiindex.
        flows_in_cols (bool, optional): If the flows are in the columns. Defaults to True.

    Returns:
        dict: Dictionary in the form of {flow: [process, process]}
    """
    flows = io_df.columns
    io_dict = {f: [] for f in flows}  # type: dict[str, list]
    index_tuples = list(io_df.stack().index) if not by_element else list(io_df.T.stack().index)
    for p, f in index_tuples:
        io_dict.setdefault(f, []).append(p)
    return {k: v for k, v in io_dict.items() if v}  # Get rid of empty flows


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Combine two dictionaries, keeping the values of both.

    Args:
        dict1 (dict): input 1
        dict2 (dict): input 2

    Returns:
        dict: merged dictionary
    """
    keys = set(dict1.keys()) | set(dict2.keys())
    out_dict = {k: [] for k in keys}  # type: dict[str, list]
    for d in [dict1, dict2]:
        for k, i in d.items():
            out_dict[k].extend(i)

    return out_dict


def get_lf_vre(country: str) -> dict:
    """Get a dictionary with load factors for variable renewables (PV, OnshoreWind, OffshoreWind).

    Args:
        country (str): country ISO 3166-1 alpha-2 code

    Returns:
        dict: LF data, indexed by [Tech][year (1980-2019), timeslice (0-23)]
    """
    path = "data/zenodo_ivan/_common/renewables_ninja"
    solar_pv = pd.read_csv(
        f"{path}/ninja_pv_country_{country}_merra-2_corrected.csv",
        header=2,
        index_col=0,
    )
    wind = pd.read_csv(
        f"{path}/ninja_wind_country_{country}_current-merra-2_corrected.csv",
        header=2,
        index_col=0,
    )

    if len(wind.columns) > 1:
        wind.rename({"offshore": "OffshoreWind", "onshore": "OnshoreWind"}, axis=1, inplace=True)
        wind.drop("national", axis=1, inplace=True)
    else:
        wind.rename({"national": "OnshoreWind"}, axis=1, inplace=True)
        wind["OffshoreWind"] = 0

    solar_pv.index = pd.DatetimeIndex(solar_pv.index)
    wind.index = pd.DatetimeIndex(wind.index)
    solar_pv.columns = ["PV"]

    vre_df = pd.concat([solar_pv, wind], axis=1)
    result = vre_df.groupby([vre_df.index.year, vre_df.index.hour]).mean()

    col_fix = {
        "PV": "conv_elec_pv",
        "OnshoreWind": "conv_elec_onshorewind",
        "OffshoreWind": "conv_elec_offshorewind",
    }
    new_col = [col_fix[i] for i in result.columns]

    result.columns = new_col

    return result.to_dict()


class ConfigHandler:
    """Configuration file reading and extraction."""

    def __init__(self, path) -> None:
        """Initialise ConfigHandler object.

        Args:
            path (str): path to the configuration file.
        """
        # Get model configuration
        excel_file = pd.ExcelFile(path)

        fxe = {}
        params = {}

        # Convert configuration to dictionaries to improve speed
        for group in excel_file.sheet_names:
            if group in ["FiE", "FoE"]:
                fxe[group] = pd.read_excel(path, group, index_col=0)
            else:
                sheet_df = pd.read_excel(path, sheet_name=group)
                for entity_id in sheet_df.columns.drop(CNF_INDEX):
                    if entity_id in params:
                        raise ValueError("Found duplicate id", entity_id, "in sheet", group)
                    params[entity_id] = {}
                    id_cnf = sheet_df.loc[:, CNF_INDEX + [entity_id]]
                    for data_type in id_cnf["Type"].unique():
                        entity_df = id_cnf.loc[id_cnf["Type"] == data_type].copy()
                        if data_type == "annual":
                            entity_df.drop(["Type", "Flow"], axis=1, inplace=True)
                            entity_df.set_index(["Parameter", "Year"], inplace=True)
                        elif data_type == "constant":
                            entity_df.drop(["Type", "Flow", "Year"], axis=1, inplace=True)
                            entity_df.set_index(["Parameter"], inplace=True)
                        elif data_type == "constant_fxe":
                            entity_df.drop(["Type", "Year"], axis=1, inplace=True)
                            entity_df.set_index(["Parameter", "Flow"], inplace=True)
                        elif data_type == "configuration":
                            entity_df.drop(["Type", "Flow", "Year"], axis=1, inplace=True)
                            entity_df.set_index(["Parameter"], inplace=True)
                        else:
                            raise ValueError("Invalid Data Type", data_type, "in", group, entity_id)

                        params[entity_id][data_type] = entity_df.to_dict()[entity_id]

        self.fxe = fxe
        self.params = params

    def check_cnf(self, entity_id, parameter):
        """Evaluate if a configuration option is set."""
        # Turns functionality on/off. Empty values should cause deactivation, not failure.
        try:
            value = self.params[entity_id]["configuration"][parameter]
        except KeyError as exc:
            raise KeyError("Invalid key for", entity_id, parameter) from exc
        return not np.isnan(value)

    def get_const(self, entity_id: str, parameter: str) -> Any:
        """Return configuration constants."""
        # Allow empty values, but ensure usage causes error if handled improperly by returning None.
        try:
            value = self.params[entity_id]["constant"][parameter]
        except KeyError as exc:
            raise KeyError("Invalid key for", entity_id, parameter) from exc
        return value if not np.isnan(value) else None

    def get_const_fxe(self, entity_id, parameter, flow):
        """Return flow-specific constants."""
        # Allow empty values, but ensure usage causes error if handled improperly by returning None.
        try:
            value = self.params[entity_id]["constant_fxe"][(parameter, flow)]
        except KeyError as exc:
            raise KeyError("Invalid key for", entity_id, parameter, flow) from exc
        return value if not np.isnan(value) else None

    def get_annual(self, entity_id, parameter, year):
        """Return historic values."""
        # Trying to read empty annual data should cause an error to minimise bugs.
        try:
            value = self.params[entity_id]["annual"][(parameter, year)]
        except KeyError as exc:
            raise KeyError("Invalid key for", entity_id, parameter, year) from exc
        if np.isnan(value):
            raise ValueError("Requested", parameter, "in", entity_id, "is NaN. Check configuration file.")
        return value

    # Configuration sets
    def build_cnf_set(self, entity_set: set, parameter: str):
        """Create a set where the given configuration is enabled."""
        config_enabled = set()
        config_enabled = [i for i in entity_set if self.check_cnf(i, parameter)]

        return set(config_enabled)
