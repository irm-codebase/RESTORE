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
        dict: merged dictoniary
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
    
    col_fix = {"PV": "conv_elec_pv", "OnshoreWind": "conv_elec_onshorewind",
               "OffshoreWind": "conv_elec_offshorewind"}
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
        setting_names = excel_file.sheet_names
        setting_names.remove("info")

        io_dict = {}
        process_df = pd.DataFrame()
        flow_df = pd.DataFrame()
        country_df = pd.DataFrame()
        for name in setting_names:
            if "input" in name or "output" in name:
                io_dict[name] = pd.read_excel(path, name, header=1, index_col=[0, 1])
            elif "flows" == name:
                flow_df = pd.read_excel(path, name, header=0, index_col=[0, 1])
            elif "country" == name:
                country_df = pd.read_excel(path, name, header=0, index_col=[0, 1])
            else:
                tmp_df = pd.read_excel(path, name, header=0, index_col=[0, 1])
                if process_df.empty:
                    process_df = tmp_df
                else:
                    process_df = pd.merge(process_df, tmp_df, left_index=True, right_index=True, how="outer")

        # Convert configuration to dictionaries to improve speed
        self.process_cnf = process_df.to_dict()
        self.flow_cnf = flow_df.to_dict()
        self.country_cnf = country_df.to_dict()
        self.io_cnf = io_dict
        self.ef_stack = {k: i.droplevel(0).stack() for (k, i) in io_dict.items()}

    # Process functions
    # Valid for Conversion, Storage, Import and Generation types.
    def check_process_cnf(self, process: str, option: Any) -> bool:
        """See if a specific configuration is enabled for the process.

        Args:
            process (str): name of the process (e.g., conv_chp_biogas).
            option (Any): value in the second column in the process' datafile.

        Returns:
            bool: Configured value. Typically float, int or np.nan.
        """
        return not np.isnan(self.process_cnf[process][("configuration", option)])

    def get_process_cnf(self, process: str, option: Any) -> Any:
        """Get a process configuration value.

        Args:
            process (str): name of the process (e.g., conv_chp_biogas).
            value_type (str): name in the first column in the process' datafile.
            option (Any): value in the second column in the process' datafile.

        Returns:
            Any: Configured value. Typically float, int or np.nan.
        """
        return self.process_cnf[process][("configuration", option)]

    def get_process_const(self, process: str, option: Any) -> Any:
        """Get a process constant.

        Args:
            process (str): name of the process (e.g., conv_chp_biogas).
            option (Any): value in the second column in the process' datafile.

        Returns:
            Any: Configured value. Typically float, int or np.nan.
        """
        return self.process_cnf[process][("value", option)]

    def get_process_value(self, process: str, value_type: str, option: Any) -> Any:
        """Get any process value.

        Valid for Conversion, Storage, Import and Generation types.

        Args:
            process (str): name of the process (e.g., conv_chp_biogas).
            value_type (str): name in the first column in the process' datafile.
            option (Any): value in the second column in the process' datafile.

        Returns:
            Any: Configured value. Typically float, int or np.nan.
        """
        return self.process_cnf[process][(value_type, option)]
