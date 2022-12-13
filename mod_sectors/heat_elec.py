# --------------------------------------------------------------------------- #
# Filename: heat_elec.py
# Path: /heat_elec.py
# Created Date: Thursday, December 8th 2022, 4:07:28 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""D-EXPANSE model adapted for both the electricity and heat sectors.

Adapted from the simplified D-EXPANSE code.
"""

import pandas as pd
import numpy as np
import pyomo.environ as pyo


def cnf_model_indexes(mod: pyo.ConcreteModel, tech_df: pd.DataFrame, n_days: int):
    """Set the indexes to be used by the D-EXPANSE portion of the model.

    Args:
        mod (pyo.ConcreteModel): pyomo model
        tech_df (pd.DataFrame): dataframe with parsed technology data
        n_days (int): total number of k-means days
    """
    pass


def cnf_model_parameters(mod: pyo.ConcreteModel, country_df: pd.DataFrame):
    """Set parameters used throughout the model.

    Requirements: generic indexes.

    Args:
        mod (pyo.ConcreteModel): pyomo model
        country_df (pd.DataFrame): dataframe with country parameters
    """
    # Obtain yearly discount factors TODO: this should be in a generic parameter function
    pass


def cnf_model_variables(mod: pyo.ConcreteModel):
    """Create the pyomo variables used by D-EXPANSE.

    Args:
        mod (pyo.ConcreteModel): pyomo model to configure.
    """
    pass


def cnf_model_constraints(mod: pyo.ConcreteModel, tech_df: pd.DataFrame, country_df: pd.DataFrame):
    """Set constraints.

    Args:
        mod (pyo.ConcreteModel): pyomo model
        tech_df (pd.DataFrame): dataframe with technology parameters
        country_df (pd.DataFrame): dataframe with country parameters
    """
    pass


def cnf_model_objective(mod: pyo.ConcreteModel, tech_df: pd.DataFrame, country_df: pd.DataFrame):
    """Get cost expression, by first adding generic costs and then adding configuration dependent costs.

    Args:
        model (pyo.ConcreteModel): pyomo model to configure
    """
    pass


def prod_after_ownuse_y(mod: pyo.ConcreteModel, y, d, h, own_use: dict):
    """Calculate the total generation at [year, time-slice] after technology losses.

    Args:
        model (pyo.ConcreteModel): pyomo model
        y (int): year
        h (int): hour
        own_use (dict): matrix with the energy losses in the form [Tech][Year]

    Returns:
        pyo.Expression: pyomo expression of effective generation at [year, time-slice]
    """
    total_prod_output = 0
    for c in mod.DxpTechs:
        if c == "Storage":
            total_prod_output += mod.p[c, y, d, h] * (-own_use[c][y])
        else:
            total_prod_output += mod.p[c, y, d, h] * (1 - own_use[c][y])
    return total_prod_output


def get_cf_variable_renewables() -> dict:
    """Get a dataframe with capacity factors for variable renewables (PV, OnshoreWind, OffshoreWind).

    Returns:
        dict: CF data, indexed by [Tech][year (1980-2019), timeslice (0-23)]
    """
    solar_pv = pd.read_csv(
        "data/parsed/elec/ninja_pv_country_CH_merra-2_corrected.csv",
        header=2,
        index_col=0,
    )
    wind = pd.read_csv(
        "data/parsed/elec/ninja_wind_country_CH_current-merra-2_corrected.csv",
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

    return result.to_dict()


def run_d_expanse() -> pyo.ConcreteModel:
    """Run electricity only version of D-EXPANSE."""
    country_df = pd.read_excel("data/parsed/elec/Country_data_CHE.xlsx", index_col=[0, 1])
    tech_df = pd.read_excel("data/parsed/elec/Input_data_CHE.xlsx", index_col=[0, 1])
    model = pyo.ConcreteModel()
    cnf_model_indexes(model, tech_df, 2)
    cnf_model_parameters(model, country_df)
    cnf_model_variables(model)
    cnf_model_constraints(model, tech_df, country_df)
    cnf_model_objective(model, tech_df, country_df)

    opt = pyo.SolverFactory("gurobi", solver_io="python")
    opt.options["MIPGap"] = 1e-2
    opt.options["Timelimit"] = 1800
    try:
        opt_result = opt.solve(model, tee=False)
        print(opt_result)
    except ValueError:
        model.write("debug.lp", format="lp", io_options={"symbolic_solver_labels": True})
    return model


run_d_expanse()
