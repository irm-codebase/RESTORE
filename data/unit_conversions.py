# --------------------------------------------------------------------------- #
# Filename: unit_conversions.py
# Path: /unit_conversions.py
# Created Date: Thursday, October 27th 2022, 3:04:54 pm
# Author: Marc Jaxa-Rozen, Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Scripts to enable unit conversion in the Zenodo datafiles.

Adapted from the code developed by Marc.
"""
import os
import pandas as pd

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


def convert_units(row: pd.Series, new_energy="MWh", new_power="MW") -> pd.Series:
    """Convert a dataframe rows with energy or power values.

    Uses a conversion file in the _common folder.

    Args:
        row (pd.Series): a pandas dataframe row.
        new_energy (str, optional): New energy unit. Defaults to "MWh".
        new_power (str, optional): New power unit. Defaults to "MW".

    Returns:
        pd.Series: converted row, or the same as the input row if the value was not in power/energy units.
    """
    if not pd.isnull(row["Unit"]):  # Skip ratios and unit-less values

        country = row["Country"]
        parameter = row["Parameter"]
        unit = row["Unit"]
        initial_value = row["Value"]
        data_yr = row["Year"]

        # First identify the unit that will be converted.
        if "/" in unit:
            ref_unit = unit[unit.find("/") + 1:]  # For now, the script can only work with denominators
        else:
            ref_unit = unit

        # Check if the unit is configured for conversion
        if any([ref_unit in AVAILABLE_ENERGY_UNITS, ref_unit in AVAILABLE_POWER_UNITS]):
            target_unit = new_energy if ref_unit in AVAILABLE_ENERGY_UNITS else new_power
            try:
                initial_value = float(initial_value)

                # Convert to the intermediate conversion unit (MW, MWh)
                conv_factor = _get_conv_factor(country, data_yr, ref_unit)
                conv_unit = conv_factor["Unit"]
                if "/" in unit:
                    conv_value = initial_value / conv_factor["Value"]
                else:
                    conv_value = initial_value * conv_factor["Value"]

                if conv_unit != target_unit:
                    # New unit is not the intermediate unit (MW, MWh), convert again
                    conv_factor = _get_conv_factor(country, data_yr, target_unit)
                    if "/" in unit:
                        target_value = conv_value * conv_factor["Value"]
                    else:
                        target_value = conv_value / conv_factor["Value"]
                else:
                    target_value = conv_value

                if "/" in unit:
                    new_unit = unit[: unit.find("/")] + "/" + target_unit
                else:
                    new_unit = target_unit

                row["Value"] = target_value
                row["Unit"] = new_unit

            except (KeyError, IndexError, TypeError) as ex:
                print("Conversion failed for", country, parameter, data_yr, unit)
                raise Exception() from ex

    return row


def convert_currency(row: pd.DataFrame, new_cy="USD", new_yr=2019, deflator_country="local") -> pd.DataFrame:
    """Convert units and currencies.

    Supported formats: currency/(any).

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
    """Take a dataframe and fill empty values via linearisation."""
    # Clean the final dataframe
    input_df.set_index(["Entity", "Parameter", "Year"], inplace=True)
    tmp_df = input_df.copy()
    tmp_df.sort_index(inplace=True)  # Ensure the order of years is right
    # Linear interpolation across years, skipping Parameters that are not annual
    for entity in tmp_df.index.unique(level=0):
        for param in tmp_df.loc[entity].index.unique(level=0):
            idx = (entity, param, slice(None))
            data_type = tmp_df.loc[idx, "Type"].unique()
            if len(data_type) != 1:
                raise ValueError("Multiple data types used for", param, "in", entity)
            if data_type[0] == "annual":
                values = tmp_df.loc[idx, "Value"].astype(float)
                tmp_df.loc[idx, "Value"] = values.interpolate(limit_direction="both")

    input_df.update(tmp_df)

    return input_df


def create_cnf_file(data_path: str, cnf_path: str):
    """Parse through datafiles and create a configuration file, recursively."""
    dir_items = os.listdir(data_path)
    for item in dir_items:
        item_path = os.path.join(data_path, item)
        if os.path.isdir(item_path) and "_" not in item:  # ensure generic folders are omitted
            create_cnf_file(item_path, cnf_path)
        elif os.path.isfile(item_path) and "_" in item and ".xlsx" in item:
            # Get position in configuration file
            file_name = item.removesuffix(".xlsx")
            data_settings = file_name.split("_")
            if len(data_settings) != 3:
                raise ValueError("Incorrect naming in", item)
            sheet_name = data_settings[1]
            
            # Read and arrange data
            data_df = pd.read_excel(item_path, skiprows=4)
            entity = data_df["Entity"].unique()[0]
            data_df = linearise_dataframe(data_df)
            data_df.set_index(["Parameter", "Type", "Year", "Flow"], inplace=True)
            values = data_df["Value"]
            values.name = entity
            
            if os.path.isfile(cnf_path):  # Config file already exists?
                xlsx = pd.ExcelFile(cnf_path)
                if data_settings[1] in xlsx.sheet_names:
                    config_data = pd.read_excel(cnf_path, sheet_name=sheet_name)
                    config_data = pd.concat([config_data, values], axis=1)
                else:
                    config_data = values
                
                with pd.ExcelWriter(cnf_path, engine="openpyxl", mode="a") as writer:
                    config_data.to_excel(writer, sheet_name=sheet_name)
            else:
                values.to_excel(cnf_path, sheet_name=sheet_name)
