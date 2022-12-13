# --------------------------------------------------------------------------- #
# Filename: zenodo_dexp_to_restore.py
# Path: /zenodo_dexp_to_restore.py
# Created Date: Monday, December 12th 2022, 4:11:25 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""D-EXPANSE to RESTORE parser.

Converts Marc/Xin ZENODO files into my new format (with extra columns).
Necessary due to differences in scope and to reduce name ambiguity.
Post processing is required, this script only re-arranges the data and updates filenames
"""
import os
import shutil

import pandas as pd

TECH_NAME = {
    "HardCoal": "f2eh_hardcoal",
    "Gas": "f2eh_gas",
    "Oil": "f2eh_oil",
    "Nuclear": "f2eh_nuclear",
    "OnshoreWind": "f2eh_onshorewind",
    "HydroDam": "f2eh_hydrodam",
    "HydroRoR": "f2eh_hydroror",
    "PV": "f2eh_pv",
    "Biomass": "f2eh_biomass",
    "Biogas": "f2eh_biogas",
    "WasteIncineration": "f2eh_waste",
}

VAR_NAME_CHANGE = {
    "Potential_annual": "max_annual_generation",
    "Potential_installed": "max_installed_capacity",
    "Inv": "investment_cost",
    "Fuel_cost_fuel": "resource_cost",
    "Export_profit": "export_revenue",
    "ElSupplied_annual_central": "actual_supply",
    "PeakDem_fromzero_central": "peakload_demand",
    "BaseDem_central": "baseload_demand"
}

TECH_HEAT_ELEC = ["HardCoal", "Gas", "Oil", "Nuclear", "Biomass", "Biogas", "WasteIncineration"]
TECH_ELEC = ["OnshoreWind", "HydroDam", "HydroRoR", "PV"]

PATH_OLD = "data_sources/zenodo_marcxin/"
PATH_NEW = "data_sources/zenodo_ivan/"


def parse_profiles(folder: str):
    """Copy .csv profile files to the new project, ignoring peak files (unused).

    Args:
        folder (str): folder location in Marc and Xin's database.
    """
    file_list = os.listdir(folder)

    for item in file_list:
        # Skip the unused wednesday profiles
        if ".csv" in item:
            if "_wed" in item:
                continue
            else:
                item_path = os.path.join(folder, item)
                new_path = os.path.join(PATH_NEW, "profiles/electricity", item)
                shutil.copyfile(item_path, new_path)


def parse_resources(folder: str):
    
    pass


def parse_technologies(path):
    pass


def convert_all_files():
    file_list = os.listdir(PATH_OLD)
    for item in file_list:
        path = PATH_OLD + item
        match item:
            case "_common":
                parse_profiles(path)
            case "Technologies":
                parse_technologies(path)
            case "Resources":
                parse_resources(path)
            case "Profiles":
                parse_profiles(path)
            case "_":
                pass  
    pass
    
if __name__ == "__main__":
    convert_all_files()
