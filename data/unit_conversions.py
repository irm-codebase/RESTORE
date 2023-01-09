# --------------------------------------------------------------------------- #
# Filename: unit_conversions.py
# Path: /unit_conversions.py
# Created Date: Thursday, October 27th 2022, 3:04:54 pm
# Author: Marc Jaxa-Rozen, Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Scripts to enable unit conversion in the Zenodo datafiles."""
import os
import logging

import pandas as pd

COMMON_PATH = "data/zenodo_ivan/_common"

CURRENCY_DF = pd.read_csv(os.path.join(COMMON_PATH, "Currency.csv"), skiprows=4, index_col=[0, 2])

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
UNITS_DF = pd.read_csv(os.path.join(COMMON_PATH, "Conversions.csv"), skiprows=4, index_col=[0, 1, 3, 2])


class NonRepetitiveLogger(logging.Logger):
    """Simple logger for unit conversion errors."""

    def __init__(self, name, level=logging.NOTSET):
        """Set logger.

        Args:
            name (str): Name of the logger
            level (Any, optional): Lowest severity to dispatch. Defaults to logging.NOTSET.
        """
        super().__init__(name=name, level=level)
        self._message_cache = []

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        msg_hash = hash(msg)
        if msg_hash in self._message_cache:
            return
        self._message_cache.append(msg_hash)
        super()._log(level, msg, args, exc_info, extra, stack_info)


# TODO: fix logging, does not seem to work
logger = NonRepetitiveLogger("units")
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter("[%(levelname)s] - %(message)s"))
logger.addHandler(sh)
logger.setLevel(logging.INFO)
logging.Logger


def _get_conv_factor(country: str, entity: str, data_yr: int, unit_name: str):
    """Find the most specific conversion factor available in the units data file.

    E.g.: in case there are time-specific national conversion factors for energy per ton of coal, etc.

    Args:
        country (str): 3-letter ISO 3166 country code.
        entity (str): Technology of resource name found under the 'Entity' column of the dataframe.
        data_yr (int): Year of the data to be converted.
        unit_name (str): Name of the unit found under the 'Parameter' column of the dataframe.

    Returns:
        Any: conversion factor.
    """
    conv = 1.0  # Default to 1 so the script does not stop if there is an issue. Always look at the logger.
    try:
        # Specific conversion factor for country, technology, year and unit?
        # NOTE: dataframe index is left as string type to avoid mixed dtypes, so we index using str(data_yr)
        conv = UNITS_DF.loc[(country, entity, str(data_yr), unit_name)]
    except (KeyError, IndexError):
        try:
            # Specific conversion factor for country, technology, and unit?
            conv = UNITS_DF.loc[(country, entity, "Undefined", unit_name)]
        except (KeyError, IndexError):
            try:
                # Specific conversion factor for technology and unit?
                conv = UNITS_DF.loc[("Undefined", entity, "Undefined", unit_name)]
            except (KeyError, IndexError):
                try:
                    # General conversion factor for unit
                    conv = UNITS_DF.loc[("Undefined", "Undefined", "Undefined", unit_name)]
                except (KeyError, IndexError) as ex:
                    logger.debug(ex)

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
        float: _description_
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


def convert_unit(
    row: pd.DataFrame, new_cy="USD", new_yr=2019, new_energy="MWh", new_power="MW", deflator_country="local"
) -> pd.DataFrame:
    """Convert units and currencies.

    Supported formats: unit of power or energy, or currency/(unit of power or energy).

    Args:
        row (pd.DataFrame): pandas dataframe row with columns [Country, Entity, Year, Value, Unit]
        new_cy (str, optional): Currency to convert to in 3-letter ISO 4217. Defaults to "USD".
        new_yr (int, optional): New year to use as deflator. Defaults to 2019.
        new_energy (str, optional): Energy unit to convert to using MWh as intermediary. Defaults to "MWh".
        new_power (str, optional): Power unit to convert to using MW as intermediary. Defaults to "MW".
        deflator_country (str, optional): National deflator to use. Defaults to "local" (row[Country]).

    Returns:
        pd.Dataframe: row with new modified data
    """
    available_currencies = CURRENCY_DF["Parameter"].unique()

    if not pd.isnull(row["Unit"]):

        country = row["Country"]
        entity = row["Entity"]
        unit = row["Unit"]
        value = row["Value"]
        data_yr = row["Year"]

        try:
            value = float(value)
            if "/" in unit:
                # Fractions are only for currency values
                numerator = unit[: unit.find("/")]
                denominator = unit[unit.find("/") + 1:]
                if not numerator[-4:].isdigit():
                    # Year improperly formatted
                    logger.info("Error for %s: conversion not implemented (%s)", entity, unit)
                elif not numerator[:3] in available_currencies:
                    # Currency not available in common file
                    logger.info("Currency not found: %s", numerator)
                else:
                    # convert to the specified new currency and year
                    val_new_yr = _get_new_currency(row, new_cy, new_yr, deflator_country)
                    num_unit = f"{new_cy}{new_yr}"

                    conv_factor = _get_conv_factor(country, entity, data_yr, denominator)
                    conv_unit = conv_factor["Unit"]
                    new_value_refunit = val_new_yr / conv_factor["Value"]

                    if new_energy != "MWh" and conv_unit == "MWh":
                        new_value = new_value_refunit * (
                            _get_conv_factor(country, entity, data_yr, new_energy)["Value"]
                        )
                        denom_unit = new_energy
                    elif new_power != "MW" and conv_unit == "MW":
                        new_value = new_value_refunit * (
                            _get_conv_factor(country, entity, data_yr, new_power)["Value"]
                        )
                        denom_unit = new_power
                    else:
                        new_value = new_value_refunit
                        denom_unit = conv_unit

                    new_unit = f"{num_unit}/{denom_unit}"

            else:
                conv_factor = _get_conv_factor(country, entity, data_yr, unit)
                conv_unit = conv_factor["Unit"]
                new_value_refunit = value * conv_factor["Value"]

                if new_energy != "MWh" and conv_unit == "MWh":
                    new_value = new_value_refunit / (
                        _get_conv_factor(country, entity, data_yr, new_energy)["Value"]
                    )
                    conv_unit = new_energy
                elif new_power != "MW" and conv_unit == "MW":
                    new_value = new_value_refunit / (
                        _get_conv_factor(country, entity, data_yr, new_power)["Value"]
                    )
                    conv_unit = new_power
                else:
                    new_value = new_value_refunit

                new_unit = conv_unit

            row["Value"] = new_value
            row["Unit"] = new_unit

        except (KeyError, IndexError, TypeError) as ex:
            logger.debug(str(ex))

    return row