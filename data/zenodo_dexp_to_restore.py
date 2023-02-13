# --------------------------------------------------------------------------- #
# Filename: zenodo_dexp_to_restore.py
# Path: /zenodo_dexp_to_restore.py
# Created Date: Monday, December 12th 2022, 4:11:25 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""D-EXPANSE to RESTORE parsers and conversion scripts."""
import os
import shutil

import pandas as pd
import numpy as np

from gen_utils import file_manager


PATH_OLD = "/Users/ruiziv/switchdrive/ACCURACY/D-EXPANSE/CHE"
PATH_NEW = "data/zenodo_ivan/"

TECH_CHP_ABLE = ["coal", "biogas", "gas", "oil", "uranium", "waste", "biomass"]

TECH_LOWERCASE = [
    "LF_min",
    "LF_max",
    "Ramp_rate",
    "Actual_capacity",
    "Actual_new_capacity",
    "Actual_retired_capacity",
    "Learning_rate",
    "Initial_retired_capacity",
    "Lifetime",
]
TECH_RENAME_ACTIVITY = {
    "Buildrates": "buildrate",
    "Potential_annual": "max_activity_annual",
    "Potential_installed": "max_capacity_annual",
    "Inv": "cost_investment",
    "Fixed_OM_annual": "cost_fixed_om_annual",
    "Variable_OM": "cost_variable_om",
    "Actual_generation": "actual_activity",
}
TECH_RENAME_INPUT = {"Fuel_efficiency": "input_efficiency"}
TECH_RENAME_OUTPUT = {
    "Peak_contr": "output_peak_ratio",
    "Own_use": "output_efficiency",
    "Heat_to_electricity": "output_ratio",
}

COUNTRY_LOWERCASE = ["GDP_per_capita", "Population"]
COUNTRY_RENAME = {"Discount_rate_uniform": "discount_rate"}

RESOURCE_TYPE = {
    "Biogas": "generation",
    "Biomass": "generation",
    "Coal": "import",
    "Gas": "import",
    "Hydro": "generation",
    "Import": None,
    "Oil": "generation",
    "OnshoreWind": "generation",
    "Solar": "generation",
    "Storage": None,
    "Uranium": "generation",
    "Waste": "generation",
}


def convert_all_files(path_old: str, path_new: str):
    """Convert all the files in a given country folder into the new format.

    Converts Marc/Xin ZENODO files into my new format (with extra columns).
    Necessary due to differences in scope and to reduce name ambiguity.

    !!!!!!!!!!!!!!!!!!!! IMPORTANT !!!!!!!!!!!!!!!!!!!!
    Post processing is REQUIRED, this script only re-arranges the data and updates filenames.
    Look for rows with 'todo' specified in the Value column.
    !!!!!!!!!!!!!!!!!!!! IMPORTANT !!!!!!!!!!!!!!!!!!!!

    Args:
        path_old (str): path to a country folder in MarcXin's database.
        path_new (str): path where the converted files will be stored.
    """
    file_list = os.listdir(path_old)
    for item in file_list:
        item_path = os.path.join(path_old, item)
        match item:
            case "Technologies":
                parse_technologies(item_path, path_new)
            case "Resources":
                parse_resources(item_path, path_new)
            case "Profiles":
                parse_profiles(item_path, path_new)
            case _:
                if os.path.isfile(item_path) and "CountryData" in item:
                    old_df = pd.read_csv(item_path, header=4)
                    # Update country data
                    new_df = reshape_columns_to_new_format(old_df)
                    new_df = update_country_data(new_df)
                    file_manager.save_excel(new_df, path_new)
                    # Create a resource file for electricity supply
                    new_df = reshape_columns_to_new_format(old_df)
                    new_df = convert_country_to_resource(new_df)
                    file_manager.save_excel(new_df, os.path.join(path_new, "resource"))


def parse_profiles(old_folder: str, new_folder: str):
    """Copy .csv profile files to the new project, including peak files.

    Args:
        old_folder (str): profile folder location in Marc and Xin's database.
        new_folder (str): profie folder location where profiles will be moved.
    """
    file_list = os.listdir(old_folder)

    for item in file_list:
        if ".csv" in item:
            item_path = os.path.join(old_folder, item)
            save_path = os.path.join(new_folder, "profiles/elec_supply", item)
            shutil.copyfile(item_path, save_path)


def parse_technologies(old_folder: str, new_folder):
    """Identify the type of technology and convert into the new format categories (process, storage, import).

    Args:
        old_folder (str): directory where the old technology files are located.
        new_folder (str): directory where the modified process files will be stored.
    """
    file_list = os.listdir(old_folder)
    for item in file_list:
        old_path = os.path.join(old_folder, item)
        old_df = pd.read_csv(old_path, header=3)
        new_df = reshape_columns_to_new_format(old_df)
        if "Import" in item:
            new_df = update_tech_import_to_elec_import(new_df)
            save_path = os.path.join(new_folder, "import")
        elif "Storage" in item:
            new_df = convert_tech_to_pumphydro(new_df)
            save_path = os.path.join(new_folder, "storage/elec_supply")
        else:
            new_df, chp_flag = update_tech_data(new_df)
            # save new file
            if chp_flag:
                save_path = os.path.join(new_folder, "process/chp_supply")
            else:
                save_path = os.path.join(new_folder, "process/elec_supply")
        file_manager.save_excel(new_df, save_path)


def parse_resources(old_folder: str, new_folder: str):
    """Identify the type of Resource and convert into the new format categories (import, generation).

    Args:
        old_folder (str): directory where the old technology files are located.
        new_folder (str): directory where the modified process files will be stored.
    """
    file_list = os.listdir(old_folder)
    for item in file_list:
        old_path = os.path.join(old_folder, item)
        old_df = pd.read_csv(old_path, header=4)
        new_df = reshape_columns_to_new_format(old_df)
        resource_name = item[4:-12]  # remove country code and file extension from the filename
        match RESOURCE_TYPE[resource_name]:
            case None:
                continue
            case "generation":
                new_df = convert_resource_to_generation(new_df)
                save_path = os.path.join(new_folder, "generation")
            case "import":
                new_df = convert_resource_to_import(new_df)
                save_path = os.path.join(new_folder, "import")
        file_manager.save_excel(new_df, save_path)


def reshape_columns_to_new_format(old_df: pd.DataFrame) -> pd.DataFrame:
    """Copy the data of a MarcXin file into my new format.

    Args:
        old_df (pd.DataFrame): dataframe with the old D-EXPANSE file format.

    Returns:
        pd.DataFrame: new dataframe
    """
    template_df = file_manager.get_template_dataframe()

    copy_list = ["Country", "Entity", "Parameter", "Year", "Value", "Unit", "Reference", "Note"]
    new_df = pd.DataFrame(columns=template_df.columns)
    for column in old_df.columns:
        if column in copy_list:
            new_df[column] = old_df[column]

    return new_df


def update_tech_data(tech_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Update a technology dataframe into the new format.

    TODO: make this less ugly, maybe?
    Objectives: update resource/parameter names, add input/output resource flows.
    By default, all technologies are set to have 1 input (their resource) and 1 output (elecsupply).
    Only technologies with a "heat to electricity" ratio are set to have elecsupply + heatsupply
    output.
    Tests are run to verify that all parameter types have been updated.

    Args:
        tech_df (pd.DataFrame): technology dataframe as taken from the MarcXin .csv file.

    Raises:
        ValueError: In case that not all parameters were identified/modified.


    Returns:
        tuple[pd.DataFrame, bool]: (Updated Dataframe, flag for CHP plants)
    """
    # Get the input resource
    tmp_df = tech_df.loc[tech_df["Parameter"] == "Resource"]
    input_resource = tmp_df.loc[0, "Value"]
    input_resource = str.lower(input_resource.replace("Resource", ""))

    # Detect if this is a CHP technology
    chp_flag = bool(input_resource in TECH_CHP_ABLE)

    # Mark current data for future deletion
    tech_df["Delete"] = "MarcXin"

    param_list = tech_df["Parameter"].value_counts().index.to_list()
    for param in param_list:
        # Fix resource
        if param == "Resource":
            tmp_df = tech_df.loc[tech_df["Parameter"] == param].copy()
            input_resource = tmp_df.loc[0, "Value"]
            input_resource = str.lower(input_resource.replace("Resource", ""))
            tmp_df["Value"] = input_resource
            tmp_df["Parameter"] = "input_resource"
            tech_df.update(tmp_df)
        # Change parameter to lowercase
        elif param in TECH_LOWERCASE:
            tech_df = tech_df.replace(param, str.lower(param))
        # Change parameters with new name
        elif param in TECH_RENAME_ACTIVITY:
            tech_df = tech_df.replace(param, TECH_RENAME_ACTIVITY[param])
        # Change parameters that are input related
        elif param in TECH_RENAME_INPUT:
            tmp_df = tech_df.loc[tech_df["Parameter"] == param].copy()
            tmp_df["Parameter"] = TECH_RENAME_INPUT[param]
            tmp_df["Option"] = input_resource
            tech_df.update(tmp_df)
        # Change parameters that are output related
        elif param in TECH_RENAME_OUTPUT:
            # Update the regular electricity value
            tmp_df = tech_df.loc[tech_df["Parameter"] == param].copy()
            tmp_df["Parameter"] = TECH_RENAME_OUTPUT[param]
            tmp_df["Option"] = "elecsupply"
            if param == "Own_use":
                # Standardise to efficiency to improve code simplicity
                tmp_df["Value"] = 1 - tmp_df["Value"].astype(float)
            if param == "Heat_to_electricity":
                tmp_df["Value"] = 1
            tech_df.update(tmp_df)
            if chp_flag:
                # Create an empty heat value and mark it for updates
                tmp_df["Option"] = "heatsupply"
                tmp_df["Value"] = "TODO: find"
                tmp_df.loc[:, "Unit":] = np.nan
                tech_df = pd.concat([tech_df, tmp_df])
        else:
            raise ValueError("Parameter value(s) not in lookup options:", param)

    # Update the entity in all rows
    entity = str.lower(tech_df.loc[0, "Entity"])
    if chp_flag:
        tech_df["Entity"] = "p_chp_" + entity
    else:
        tech_df["Entity"] = "p_elec_" + entity

    # Create and fill a generic dataframe
    generic_df = tech_df.loc[tech_df["Parameter"] == "input_resource"].copy()
    generic_df["Parameter"] = np.nan
    generic_df.loc[:, "Period":] = np.nan
    generic_df["Value"] = "TODO: find"

    # Add new activity-dependent parameters
    param = "co2_factor"
    tmp_df = generic_df.copy()
    tmp_df["Parameter"] = param
    tmp_df["Value"] = "TODO: find factor"
    tech_df = pd.concat([tech_df, tmp_df])

    # Add new input-related parameters
    for param in ["input_ratio", "input_factor"]:
        tmp_df = generic_df.copy()
        tmp_df["Parameter"] = param
        tmp_df["Option"] = input_resource
        tmp_df["Value"] = 1
        tech_df = pd.concat([tech_df, tmp_df])

    # Add new output-related parameters
    param = "output_resource"
    tmp_df = generic_df.copy()
    tmp_df["Parameter"] = param
    if chp_flag:
        tmp_df["Value"] = "elecsupply,heatsupply"
    else:
        tmp_df["Value"] = "elecsupply"
    tech_df = pd.concat([tech_df, tmp_df])

    param = "output_factor"
    tmp_df = generic_df.copy()
    tmp_df["Parameter"] = param
    tmp_df["Option"] = "elecsupply"
    if chp_flag:
        tmp_df["Value"] = "TODO: find factor"
    else:
        tmp_df["Value"] = 1
    tech_df = pd.concat([tech_df, tmp_df])
    if chp_flag:
        tmp_df["Option"] = "heatsupply"
        tmp_df["Value"] = "TODO: find factor"
    tech_df = pd.concat([tech_df, tmp_df])

    # Rearrange the data in an easy to read manner
    tech_df = tech_df.sort_values(["Parameter", "Option", "Year"])
    tech_df.reset_index(drop=True, inplace=True)

    return tech_df, chp_flag


def update_tech_import_to_elec_import(imp_df: pd.DataFrame) -> pd.DataFrame:
    """Update the old Import technology into a resource-specific configuration.

    Args:
        imp_df (pd.DataFrame): dataframe in old format (MarcXin).

    Raises:
        ValueError: if a parameter was not covered by the tests.

    Returns:
        pd.DataFrame: formatted dataframe.
    """
    params_import_from_tech = {
        "actual_capacity": "Actual_capacity",
        "actual_export": None,
        "actual_import": None,
        "actual_new_capacity": "Actual_new_capacity",
        "actual_retired_capacity": "Actual_retired_capacity",
        "buildrate": "Buildrates",
        "co2_factor": None,
        "cost_fixed_om_annual": "Fixed_OM_annual",
        "cost_import": None,
        "cost_investment": "Inv",
        "cost_variable_om": "Variable_OM",
        "efficiency": "Fuel_efficiency",
        "enable_import": None,
        "enable_export": None,
        "initial_retired_capacity": "Initial_retired_capacity",
        "learning_rate": "Learning_rate",
        "lf_max": "LF_max",
        "lf_min": "LF_min",
        "lifetime": "Lifetime",
        "max_activity_annual": "Potential_annual",
        "max_capacity_annual": "Potential_installed",
        "ramp_rate": "Ramp_rate",
        "resource": "Resource",
        "revenue_export": None,
    }
    # Mark current data for future deletion
    imp_df["Delete"] = "MarcXin"

    old_params = imp_df["Parameter"].value_counts().index.to_list()

    for new, old in params_import_from_tech.items():
        if old == "Resource":
            tmp_df = imp_df.loc[imp_df["Parameter"] == old].copy()
            tmp_df["Value"] = "elecsupply"
            tmp_df["Parameter"] = new
            imp_df.update(tmp_df)
            old_params.remove(old)
        elif old is None:
            generic_df = imp_df.loc[imp_df["Parameter"] == "actual_capacity"].copy()
            generic_df["Parameter"] = new
            generic_df.loc[:, "Period":] = np.nan
            generic_df["Value"] = "TODO: find"
            imp_df = pd.concat([imp_df, generic_df])
        else:
            imp_df.replace(old, new, inplace=True)
            old_params.remove(old)

    for old in old_params:
        index = imp_df.loc[imp_df["Parameter"] == old].index
        imp_df.drop(index, inplace=True)

    # Rearrange the data in an easy to read manner
    imp_df = imp_df.sort_values(["Parameter", "Option", "Year"])
    imp_df.reset_index(drop=True, inplace=True)

    # Update the entity in all rows
    imp_df["Entity"] = "imp_elecsupply"

    return imp_df


def convert_resource_to_generation(gen_df: pd.DataFrame) -> pd.DataFrame:
    """Update an old Resource file into a generation entity.

    Args:
        gen_df (pd.DataFrame): Resource dataframe in old format (MarcXin).

    Returns:
        pd.DataFrame: formatted generation dataframe.
    """
    params_generation_from_resource = {
        "cost_generation": "Fuel_cost_fuel",
        "max_activity_annual": None,
        "proven_reserves": None,
        "resource": None,
    }

    # Mark current data for future deletion
    gen_df["Delete"] = "MarcXin"

    entity = str.lower(gen_df.loc[0, "Entity"]).replace("resource", "")

    old_params = gen_df["Parameter"].value_counts().index.to_list()
    for new, old in params_generation_from_resource.items():
        if old is None:
            generic_df = gen_df.loc[gen_df["Parameter"] == "cost_generation"].copy()
            generic_df["Parameter"] = new
            generic_df.loc[:, "Period":] = np.nan
            if new == "resource":
                generic_df["Value"] = entity
            else:
                generic_df["Value"] = "TODO: find"
            gen_df = pd.concat([gen_df, generic_df])
        else:
            gen_df.replace(old, new, inplace=True)
            old_params.remove(old)

    # Remove unnecessary parameters
    for old in old_params:
        index = gen_df.loc[gen_df["Parameter"] == old].index
        gen_df.drop(index, inplace=True)

    # Update the entity in all rows
    gen_df["Entity"] = "gen_" + entity

    # Rearrange the data in an easy to read manner
    gen_df = gen_df.sort_values(["Parameter", "Option", "Year"])
    gen_df.reset_index(drop=True, inplace=True)

    return gen_df


def convert_resource_to_import(imp_df: pd.DataFrame) -> pd.DataFrame:
    """Update an old Resource file into an import entity.

    Args:
        gen_df (pd.DataFrame): Resource dataframe in old format (MarcXin).

    Returns:
        pd.DataFrame: formatted generation dataframe.
    """
    new_param_builder = {
        "actual_capacity": None,
        "actual_export": None,
        "actual_import": True,
        "actual_new_capacity": None,
        "actual_retired_capacity": None,
        "buildrate": None,
        "co2_factor": True,
        "cost_fixed_om_annual": None,
        "cost_import": "Fuel_cost_fuel",
        "cost_investment": None,
        "cost_variable_om": None,
        "efficiency": 1,
        "enable_import": 1,
        "enable_export": 0,
        "initial_retired_capacity": None,
        "learning_rate": None,
        "lf_max": None,
        "lf_min": None,
        "lifetime": None,
        "max_activity_annual": True,
        "max_capacity_annual": None,
        "ramp_rate": None,
        "resource": True,
        "revenue_export": None,
        "enable_capacity": 0,
    }

    # Mark current data for future deletion
    imp_df["Delete"] = "MarcXin"

    resource = str.lower(imp_df.loc[0, "Entity"]).replace("resource", "")

    generic_df = imp_df.loc[imp_df["Parameter"] == "Fuel_cost_fuel"].copy()
    generic_df["Parameter"] = np.nan
    generic_df.loc[:, "Period":] = np.nan
    generic_df["Value"] = "TODO: find"

    old_params = imp_df["Parameter"].value_counts().index.to_list()
    for new_param, value in new_param_builder.items():
        if isinstance(value, str):
            # String indicate that the parameter value is present in the old file
            imp_df.replace(value, new_param, inplace=True)
            old_params.remove(value)
        elif value is not None:
            # Otherwise, prefill with generic data
            tmp_df = generic_df.copy()
            tmp_df["Parameter"] = new_param
            if isinstance(value, bool):
                if new_param == "resource":
                    tmp_df["Value"] = resource
                else:
                    tmp_df["Value"] = "TODO: find"
            else:
                tmp_df["Value"] = value
            imp_df = pd.concat([imp_df, tmp_df])

    # Remove unnecessary parameters
    for value in old_params:
        index = imp_df.loc[imp_df["Parameter"] == value].index
        imp_df.drop(index, inplace=True)

    # Update the entity in all rows
    imp_df["Entity"] = "imp_" + resource

    # Rearrange the data in an easy to read manner
    imp_df = imp_df.sort_values(["Parameter", "Option", "Year"])
    imp_df.reset_index(drop=True, inplace=True)

    return imp_df


def convert_tech_to_pumphydro(sto_df: pd.DataFrame) -> pd.DataFrame:
    """Update the old Storage technology into a resource-specific configuration.

    Args:
        sto_df (pd.DataFrame): dataframe in old format (MarcXin).

    Raises:
        ValueError: if a parameter was not covered by the tests.

    Returns:
        pd.DataFrame: formatted dataframe.
    """
    params_storage_from_tech = {
        "actual_activity": "Actual_generation",
        "actual_capacity": "Actual_capacity",
        "actual_new_capacity": "Actual_new_capacity",
        "actual_retired_capacity": "Actual_retired_capacity",
        "buildrate": "Buildrates",
        "co2_factor": None,
        "cost_fixed_om_annual": "Fixed_OM_annual",
        "cost_investment": "Inv",
        "cost_variable_om": "Variable_OM",
        "efficiency": "Own_use",
        "initial_retired_capacity": "Initial_retired_capacity",
        "learning_rate": "Learning_rate",
        "lf_max": "LF_max",
        "lf_min": "LF_min",
        "lifetime": "Lifetime",
        "max_activity_annual": "Potential_annual",
        "max_capacity_annual": "Potential_installed",
    }

    # Mark current data for future deletion
    sto_df["Delete"] = "MarcXin"
    old_params = sto_df["Parameter"].value_counts().index.to_list()

    for new, old in params_storage_from_tech.items():
        if old in ("Resource", "Own_use"):
            # Update the resource parameter values in specific cases
            tmp_df = sto_df.loc[sto_df["Parameter"] == old].copy()
            match old:
                case "Resource":
                    tmp_df["Value"] = "elecsupply"
                case "Own_use":
                    tmp_df["Value"] = 1 - tmp_df["Value"].astype(float)  # Standardised efficiency
            tmp_df["Parameter"] = new
            sto_df.update(tmp_df)
            old_params.remove(old)
        elif old is None:
            # Add new parameters and mark them for data-search activities
            generic_df = sto_df.loc[sto_df["Parameter"] == "actual_capacity"].copy()
            generic_df["Parameter"] = new
            generic_df.loc[:, "Period":] = np.nan
            generic_df["Value"] = "TODO: find"
            sto_df = pd.concat([sto_df, generic_df])
        else:
            # Rename other parameters, keeping data intact
            sto_df.replace(old, new, inplace=True)
            old_params.remove(old)

    for old in old_params:
        # Remove all unnecessary parameters
        index = sto_df.loc[sto_df["Parameter"] == old].index
        sto_df.drop(index, inplace=True)

    # Rearrange the data in an easy to read manner
    sto_df = sto_df.sort_values(["Parameter", "Option", "Year"])
    sto_df.reset_index(drop=True, inplace=True)

    # Update the entity in all rows
    # Update the entity in all rows
    sto_df["Entity"] = "stor_elecsupply_pumpedhydro"

    return sto_df


def update_country_data(country_df: pd.DataFrame) -> pd.DataFrame:
    """Update country file by renaming parameters and removing resource related entries.

    Args:
        country_df (pd.DataFrame): country dataframe in old format.

    Returns:
        pd.DataFrame: updated dataframe.
    """
    # Mark current data for future deletion
    country_df["Delete"] = "MarcXin"

    param_list = country_df["Parameter"].value_counts().index.to_list()
    for param in param_list:
        if param in COUNTRY_LOWERCASE:
            country_df = country_df.replace(param, str.lower(param))
        elif param in COUNTRY_RENAME:
            country_df = country_df.replace(param, COUNTRY_RENAME[param])
        else:
            index = country_df.loc[country_df["Parameter"] == param].index
            country_df.drop(index, inplace=True)

    # Update the entity in all rows
    country_df["Entity"] = "country"

    # Rearrange the data in an easy to read manner
    country_df = country_df.sort_values(["Parameter", "Option", "Year"])
    country_df.reset_index(drop=True, inplace=True)

    return country_df


def convert_country_to_resource(country_df: pd.DataFrame) -> pd.DataFrame:
    """Convert the country data file into a resource file.

    Args:
        country_df (pd.DataFrame): country dataframe in old format.

    Returns:
        pd.DataFrame: updated dataframe.
    """
    params_resource_from_country = {
        "min_base_capacity": "BaseDem_central",
        "min_peak_capacity": "PeakDem_fromzero_central",
        "capacity_margin": "Capacity_margin",
        "actual_resource": "ElSupplied_annual_central",
    }

    # Mark current data for future deletion
    country_df["Delete"] = "MarcXin"

    old_params = country_df["Parameter"].value_counts().index.to_list()
    for new, old in params_resource_from_country.items():
        country_df.replace(old, new, inplace=True)
        old_params.remove(old)

    for old in old_params:
        index = country_df.loc[country_df["Parameter"] == old].index
        country_df.drop(index, inplace=True)

    # Rearrange the data in an easy to read manner
    country_df = country_df.sort_values(["Parameter", "Option", "Year"])
    country_df.reset_index(drop=True, inplace=True)

    # Update the entity in all rows
    country_df["Entity"] = "elecsupply"

    return country_df


if __name__ == "__main__":
    convert_all_files(PATH_OLD, PATH_NEW)
