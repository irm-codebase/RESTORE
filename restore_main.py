# --------------------------------------------------------------------------- #
# Filename: restore_main.py
# Path: /restore_main.py
# Created Date: Thursday, December 8th 2022, 4:36:17 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Main model file."""

import pyomo.environ as pyo


def set_main_indexes(mod: pyo.ConcreteModel, tech_df: pd.DataFrame, n_days: int):
    """Set the indexes to be used by the D-EXPANSE portion of the model.

    Args:
        mod (pyo.ConcreteModel): pyomo model
        tech_df (pd.DataFrame): dataframe with parsed technology data
        n_days (int): total number of k-means days
    """
    mod.Years = pyo.Set(initialize=tech_df.loc["Actual_capacity"].index)
    mod.DxpCols = pyo.Set(initialize=tech_df.columns)
    tech = tech_df.columns.drop("Import")
    mod.DxpTechs = pyo.Set(initialize=tech)
    mod.DxpDays = pyo.RangeSet(0, n_days - 1)
    mod.DxpHours = pyo.RangeSet(0, 24 - 1)