# --------------------------------------------------------------------------- #
# Filename: zenodo_to_cnf.py
# Path: /zenodo_to_cnf.py
# Created Date: Thursday, October 27th 2022, 3:04:54 pm
# Author: Marc Jaxa-Rozen, Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Converting Zenodo datafiles to a configuration file.

Unit conversion and currency conversion functions were adapted from D-EXPANSE.
Linearisation and configuration data aggregation are new to RESTORE.
"""
import os
import pandas as pd
import numpy as np

COMMON_PATH = "data/zenodo_ivan/_common"

CURRENCY_DF = pd.read_csv(os.path.join(COMMON_PATH, "Currency.csv"), skiprows=4, index_col=[0, 2])
AVAILABLE_CURRENCIES = CURRENCY_DF["Parameter"].unique()

# Currency exchange rates to USD, indexed by currency and year
EXCHANGE_RATE_DF = (
    CURRENCY_DF[CURRENCY_DF["Parameter"] != "ReferenceCurrency"]
    .reset_index()
    .set_index(["Parameter", "Year"])
    .copy()
    .apply(pd.to_numeric, errors="ignore")
)
# Reference national currency indexed by country and year
REF_CURRENCY_DF = (
    CURRENCY_DF[CURRENCY_DF["Parameter"] == "ReferenceCurrency"].reset_index().set_index(["Country", "Year"])
)
# GDP deflator indexed by country and year
DEFLATOR_DF = pd.read_csv(os.path.join(COMMON_PATH, "Deflator.csv"), skiprows=4, index_col=[0, 2])

# Units indexed by country, technology, year, unit
UNITS_DF = pd.read_csv(os.path.join(COMMON_PATH, "Conversions.csv"), skiprows=4, index_col=[0, 2, 1])
AVAILABLE_POWER_UNITS = UNITS_DF.loc[UNITS_DF["Unit"] == "MW"].index.unique(2)
AVAILABLE_ENERGY_UNITS = UNITS_DF.loc[UNITS_DF["Unit"] == "MWh"].index.unique(2)

CNF_INDEX = ["Type", "Parameter", "Flow", "Year"]
ZENODO_FOLDER_PATH = "data/zenodo_ivan"


def _get_conv_factor(country: str, data_yr: int, unit_name: str):
    """Find the most specific conversion factor available in the units data file.

    By default, all units are converted to/from MW or MWh.
    E.g., converting from nation and year specific energy units into TWh requires two calls.
    GBR oil tonne * conv_factor(GBR,year,tonne_oil) -> MWh / conv_factor(_,_,_,TWh)-> TWh

    Args:
        country (str): 3-letter ISO 3166 country code.
        data_yr (int): Year of the data to be converted.
        unit_name (str): Name of the energy/power unit. E.g., "GW, PJ, tonne_coal, ktoe".

    Returns:
        Any: conversion factor.
    """
    conv = 1.0  # Default to 1 so the script does not stop if there is an issue. Always look at the logs.
    try:
        # Specific conversion factor for country, year and unit?
        # NOTE: dataframe index is left as string type to avoid mixed dtypes, so we index using str(data_yr)
        conv = UNITS_DF.loc[(country, str(data_yr), unit_name)]
    except (KeyError, IndexError):
        try:
            # Specific conversion factor for country, and unit?
            conv = UNITS_DF.loc[(country, "Undefined", unit_name)]
        except (KeyError, IndexError):
            try:
                # General conversion factor for unit?
                conv = UNITS_DF.loc[("Undefined", "Undefined", unit_name)]
            except (KeyError, IndexError) as ex:
                print("Conversion factor not found for", country, data_yr, unit_name)
                raise Exception() from ex

    return conv


def _get_new_currency(row: pd.DataFrame, new_currency: str, new_year: str, deflator_country: str) -> float:
    """Convert the current currency value to the specified new currency_year.

    By default, currency conversion uses Method 2 in Turner et al. 2019 :
        1. convert from the currency used in reference data to the national currency
        2. inflate from the reference data year to the desired new year using national GDP deflator
        3. convert from the national currency to the new desired currency
    See https://doi.org/10.1016/j.jval.2019.03.021 for more information.

    USD is used as an intermediate step in the following cases:
    - The reference currency is not the country's national currency.
    - The national currency changed over time (e.g., the Euro was introduced)
    - The new currency is not the national currency

    Args:
        row (pd.DataFrame): pandas row, with columns [Country, Value, Unit]
        new_currency (str): The currency to convert to.
        new_year (str): The year of the new currency (to account for inflation/deflation)
        deflator_country (str): intermediate deflator country ("local" means the current country will be used)

    Returns:
        float: new currency value
    """
    country = row["Country"]
    value = float(row["Value"])
    unit = row["Unit"]
    numerator = unit[: unit.find("/")]

    # Get reference currency and year
    ref_currency = numerator[:3]
    ref_currency_year = int(numerator[-4:])
    # Get national currency at reference year
    nat_currency_ref_year = REF_CURRENCY_DF.loc[(country, ref_currency_year), "Value"]
    # Get national currency in new year
    nat_currency_new_year = REF_CURRENCY_DF.loc[(country, new_year), "Value"]

    # Calculate deflator index
    if deflator_country == "local":
        deflator_country = country
    if new_year != ref_currency_year:
        deflator_idx = (
            DEFLATOR_DF.loc[(deflator_country, new_year), "Value"]
            / DEFLATOR_DF.loc[(deflator_country, ref_currency_year), "Value"]
        )
    else:
        deflator_idx = 1

    if nat_currency_new_year != nat_currency_ref_year or nat_currency_new_year != ref_currency:
        # National currency changed over the period or dataframe uses a different currency
        # Convert the reference using USD as intermediate step.
        # USD rate for the new currency needs to be available for reference year
        val_refyr_nat = (
            value
            * EXCHANGE_RATE_DF.loc[(ref_currency, ref_currency_year), "Value"]
            / EXCHANGE_RATE_DF.loc[(nat_currency_new_year, ref_currency_year), "Value"]
        )
    else:
        # New national currency, national reference and dataframe value are the same
        val_refyr_nat = value

    if new_currency != nat_currency_new_year:
        # New currency does not match new national currency
        # Convert with intermediate USD and deflate
        val_new_yr = (
            val_refyr_nat
            * deflator_idx
            * EXCHANGE_RATE_DF.loc[(nat_currency_new_year, new_year), "Value"]
            / EXCHANGE_RATE_DF.loc[(new_currency, new_year), "Value"]
        )
    else:
        # Otherwise, apply deflator directly
        val_new_yr = val_refyr_nat * deflator_idx

    return val_new_yr


def _convert_numerator_unit(row, new_energy, new_power):
    """Convert the numerator of a row."""
    country = row["Country"]
    parameter = row["Parameter"]
    unit = row["Unit"]
    initial_value = row["Value"]
    data_yr = row["Year"]

    if "/" in unit:
        ref_unit = unit[: unit.find("/")]  # Get numerator
    else:
        ref_unit = unit

    if any([ref_unit in AVAILABLE_ENERGY_UNITS, ref_unit in AVAILABLE_POWER_UNITS]):
        target_unit = new_energy if ref_unit in AVAILABLE_ENERGY_UNITS else new_power
        try:
            initial_value = float(initial_value)

            # Convert to the intermediate conversion unit (MW, MWh)
            conv_factor = _get_conv_factor(country, data_yr, ref_unit)
            conv_unit = conv_factor["Unit"]
            conv_value = initial_value * conv_factor["Value"]

            if conv_unit != target_unit:
                # New unit is not the intermediate unit (MW, MWh), convert again
                conv_factor = _get_conv_factor(country, data_yr, target_unit)
                target_value = conv_value / conv_factor["Value"]
            else:
                target_value = conv_value

            if "/" in unit:
                new_unit = target_unit + "/" + unit[unit.find("/") + 1:]
            else:
                new_unit = target_unit

            row["Value"] = target_value
            row["Unit"] = new_unit

        except (KeyError, IndexError, TypeError) as ex:
            print("Conversion failed for", country, parameter, data_yr, unit)
            raise Exception() from ex

    return row


def _convert_denominator_unit(row, new_energy, new_power):
    """Convert the denominator of a row."""
    country = row["Country"]
    parameter = row["Parameter"]
    unit = row["Unit"]
    initial_value = row["Value"]
    data_yr = row["Year"]

    # First identify the unit that will be converted.
    if "/" in unit:
        ref_unit = unit[unit.find("/") + 1:]  # For now, the script can only work with denominators
    else:
        raise ValueError("No denominator unit in", parameter, data_yr, ". Found", unit)

    # Check if the unit is configured for conversion
    if any([ref_unit in AVAILABLE_ENERGY_UNITS, ref_unit in AVAILABLE_POWER_UNITS]):
        target_unit = new_energy if ref_unit in AVAILABLE_ENERGY_UNITS else new_power
        try:
            initial_value = float(initial_value)

            # Convert to the intermediate conversion unit (MW, MWh)
            conv_factor = _get_conv_factor(country, data_yr, ref_unit)
            conv_unit = conv_factor["Unit"]
            conv_value = initial_value / conv_factor["Value"]

            if conv_unit != target_unit:
                # New unit is not the intermediate unit (MW, MWh), convert again
                conv_factor = _get_conv_factor(country, data_yr, target_unit)
                target_value = conv_value * conv_factor["Value"]
            else:
                target_value = conv_value

            new_unit = unit[: unit.find("/")] + "/" + target_unit

            row["Value"] = target_value
            row["Unit"] = new_unit

        except (KeyError, IndexError, TypeError) as ex:
            print("Conversion failed for", country, parameter, data_yr, unit)
            raise Exception() from ex

    return row


def convert_units(row: pd.Series, new_energy="MWh", new_power="MW") -> pd.Series:
    """Convert a dataframe rows with energy or power values.

    Uses a conversion file in the _common folder.
    Works for both numerator/denominator.

    Args:
        row (pd.Series): a pandas dataframe row.
        new_energy (str, optional): New energy unit. Defaults to "MWh".
        new_power (str, optional): New power unit. Defaults to "MW".

    Returns:
        pd.Series: converted row, or the same as the input row if the value was not in power/energy units.
    """
    if not pd.isnull(row["Unit"]):  # Skip ratios and unit-less values

        unit = row["Unit"]
        row = _convert_numerator_unit(row, new_energy, new_power)
        if "/" in unit:
            row = _convert_denominator_unit(row, new_energy, new_power)  # convert denominators if necessary

    return row


def convert_currency(row: pd.DataFrame, new_cy="USD", new_yr=2019, deflator_country="local") -> pd.DataFrame:
    """Convert units and currencies.

    Supported formats: currency/(any). ONLY WORKS FOR NUMERATORS.

    Args:
        row (pd.DataFrame): pandas dataframe row with columns [Country, Entity, Year, Value, Unit]
        new_cy (str, optional): Currency to convert to in 3-letter ISO 4217. Defaults to "USD".
        new_yr (int, optional): New year to use as deflator. Defaults to 2019.
        deflator_country (str, optional): National deflator to use. Defaults to "local" (row[Country]).

    Returns:
        pd.Dataframe: row with new modified data
    """
    if not pd.isnull(row["Unit"]):
        entity = row["Entity"]
        unit = row["Unit"]
        value = row["Value"]
        try:
            value = float(value)
            if "/" in unit:
                # Fractions are only for currency values
                numerator = unit[: unit.find("/")]
                if numerator[:3] in AVAILABLE_CURRENCIES:
                    if numerator[-4:].isdigit():
                        # convert to the specified new currency and year
                        new_value = _get_new_currency(row, new_cy, new_yr, deflator_country)
                        new_unit = f"{new_cy}{new_yr}" + unit[unit.find("/"):]

                        row["Value"] = new_value
                        row["Unit"] = new_unit
                    else:
                        # Year improperly formatted
                        raise ValueError(f"Error for {entity}: conversion not implemented ({unit})")
                else:
                    # Currency not available in common file
                    print(f"Currency not found: {numerator}")
        except (KeyError, IndexError, TypeError) as ex:
            raise Exception() from ex

    return row


def linearise_dataframe(input_df: pd.DataFrame) -> pd.DataFrame:
    """Take a dataframe and fill empty values via linearisation.

    Modifies the input dataframe!

    Args:
        input_df (pd.DataFrame): _description_

    Raises:
        ValueError: _description_

    Returns:
        pd.DataFrame: _description_
    """
    # Clean the final dataframe
    input_df.set_index(["Entity", "Parameter", "Year", "Flow"], inplace=True)
    tmp_df = input_df.copy()
    tmp_df.sort_index(inplace=True)  # Ensure the order of years is right
    # Linear interpolation across years, skipping Parameters that are not annual
    for entity in tmp_df.index.unique(level=0):
        for param in tmp_df.loc[entity].index.unique(level=0):
            idx = (entity, param, slice(None))
            data_type = tmp_df.loc[idx, "Type"].unique()
            if len(data_type) != 1:
                raise ValueError("Multiple data types used for", param, "in", entity)
            if data_type[0] in ["annual", "annual_fxe"]:
                values = tmp_df.loc[idx, "Value"].astype(float)
                tmp_df.loc[idx, "Value"] = values.interpolate(limit_direction="both")

    input_df.update(tmp_df)
    input_df.reset_index(inplace=True)

    return input_df


def create_cnf_file(data_folder_path: str, cnf_file_path: str):
    """Parse through datafiles and create a configuration file, recursively."""
    dir_items = sorted(os.listdir(data_folder_path))
    for item in dir_items:
        try:
            item_path = os.path.join(data_folder_path, item)
            if os.path.isdir(item_path) and "_" not in item:  # ensure generic folders are omitted
                create_cnf_file(item_path, cnf_file_path)
            elif os.path.isfile(item_path) and "_" in item and ".xlsx" in item and "$" not in item:
                # Test if the file is named correctly and identify the excel sheet grouping
                file_name = item.removesuffix(".xlsx")
                data_settings = file_name.split("_")
                if len(data_settings) != 3:
                    raise ValueError("Incorrect naming in", item)
                sheet_name = data_settings[1]

                # Read and arrange data (unit conversion, linearisation)
                zenodo_file_df = pd.read_excel(item_path, skiprows=4)
                zenodo_file_df = zenodo_file_df.apply(convert_units, new_power="GW", new_energy="TWh", axis=1)
                zenodo_file_df = zenodo_file_df.apply(
                    convert_currency, new_cy="EUR", new_yr=2019, deflator_country="local", axis=1
                )
                zenodo_file_df = linearise_dataframe(zenodo_file_df)

                # Construct the column to be put in the configuration file
                entity = zenodo_file_df["Entity"].unique()[0]
                zenodo_file_df.set_index(CNF_INDEX, inplace=True)
                zenodo_values = zenodo_file_df["Value"]
                zenodo_values.name = entity

                if os.path.isfile(cnf_file_path):
                    # Config file already exists
                    xlsx = pd.ExcelFile(cnf_file_path)
                    if sheet_name in xlsx.sheet_names:
                        # Combine with other columns if the sheet already exists
                        cnf_file_df = pd.read_excel(cnf_file_path, sheet_name=sheet_name)
                        cnf_file_df.set_index(CNF_INDEX, inplace=True)
                        cnf_file_df = pd.concat([cnf_file_df, zenodo_values], axis=1)
                    else:
                        # Otherwise, create the sheet
                        cnf_file_df = zenodo_values
                    cnf_file_df.sort_index(level=[0, 1], ascending=True, inplace=True)
                    # pylint: disable=abstract-class-instantiated
                    writer = pd.ExcelWriter(
                        cnf_file_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
                    )
                    with writer:
                        cnf_file_df.to_excel(writer, sheet_name=sheet_name, merge_cells=False)
                else:
                    zenodo_values.to_excel(cnf_file_path, sheet_name=sheet_name, merge_cells=False)
        except ValueError as exc:
            raise ValueError("File creation error at", item) from exc


def create_fxe_matrix(cnf_file_path: str):
    """Create sheets for FiE (flow into element) and FoE (flow out of element)."""
    xlsx = pd.ExcelFile(cnf_file_path)
    fie_matrix = pd.DataFrame()
    foe_matrix = pd.DataFrame()
    for sheet in xlsx.sheet_names:
        sheet_df = pd.read_excel(cnf_file_path, sheet_name=sheet)

        # TODO: consider combining these into one procedure (specifying sheet name and constant_fxe parm.)
        # TODO: perhaps a single configuration_fxe value (not related to efficiency) would be more flexible...
        # Get flows into elements
        sheet_fie = sheet_df.loc[
            (sheet_df["Type"] == "constant_fxe") & (sheet_df["Parameter"] == "input_efficiency")
        ]
        if not sheet_fie.empty:
            sheet_fie = sheet_fie.drop(["Type", "Parameter", "Year"], axis=1)
            for i in sheet_fie.index:
                elements = sheet_fie.columns.drop("Flow")
                flow = sheet_fie.loc[i, "Flow"]
                values = sheet_fie.loc[i, elements]
                flow_elements = pd.Series(name=flow, index=elements, data=values)
                fie_matrix = pd.concat([fie_matrix, flow_elements], axis=1)

        # Get flows out of elements
        sheet_foe = sheet_df.loc[
            (sheet_df["Type"] == "constant_fxe") & (sheet_df["Parameter"] == "output_efficiency")
        ]
        if not sheet_foe.empty:
            sheet_foe = sheet_foe.drop(["Type", "Parameter", "Year"], axis=1)
            for i in sheet_foe.index:
                elements = sheet_foe.columns.drop("Flow")
                values = sheet_foe.loc[i, elements]
                flow_elements = pd.Series(name=sheet_foe.loc[i, "Flow"], index=elements, data=values)
                foe_matrix = pd.concat([foe_matrix, flow_elements], axis=1)

    fie_matrix = fie_matrix.groupby(fie_matrix.columns, axis=1).agg(np.max)
    foe_matrix = foe_matrix.groupby(foe_matrix.columns, axis=1).agg(np.max)

    # Rearrange to improve readability
    fie_matrix.sort_index(ascending=True, inplace=True)
    foe_matrix.sort_index(ascending=True, inplace=True)

    # pylint: disable=abstract-class-instantiated
    writer = pd.ExcelWriter(cnf_file_path, engine="openpyxl", mode="a", if_sheet_exists="replace")
    with writer:
        fie_matrix.to_excel(writer, sheet_name="FiE")
        foe_matrix.to_excel(writer, sheet_name="FoE")


# If the script is called directly, build the configuration file in the downloads folder
if __name__ == "__main__":
    create_cnf_file(ZENODO_FOLDER_PATH, "/Users/ruiziv/Downloads/test.xlsx")
    create_fxe_matrix("/Users/ruiziv/Downloads/test.xlsx")
