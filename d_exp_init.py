# --------------------------------------------------------------------------- #
# Filename: d_exp_init.py
# Path: /d_exp_init.py
# Created Date: Thursday, November 24th 2022, 10:26:01 am
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Add D-EXPANSE into RESTORE as the electricity generation sector."""
import pandas as pd
import numpy as np
import pyomo.environ as pyo
import gen_utils.k_clustering as k_means

COUNTRY_PATH = "data/parsed/elec/Country_data_CHE.xlsx"
INPUT_PATH = "data/parsed/elec/Input_data_CHE.xlsx"


def cnf_model_indexes(mod: pyo.ConcreteModel, tech_df: pd.DataFrame, n_days: int) -> None:
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


def cnf_model_parameters(mod: pyo.ConcreteModel, country_df: pd.DataFrame):
    """Set parameters used throughout the model.

    Requirements: generic indexes.

    Args:
        mod (pyo.ConcreteModel): pyomo model
        country_df (pd.DataFrame): dataframe with country parameters
    """
    # Obtain yearly discount factors TODO: this should be in a generic parameter function
    y_0 = mod.Years.first()
    dr_uniform = country_df.loc["Discount_rate_uniform"].loc[y_0, "Value"]
    mod.p_DR = pyo.Param(initialize=dr_uniform)

    def param_discount_factor(mod, year):
        return 1 / np.power(1 + mod.p_DR, (year - mod.Years.first()))

    mod.p_DiscFactors = pyo.Param(mod.Years, initialize=param_discount_factor, doc="Discount Factors")


def cnf_model_variables(mod: pyo.ConcreteModel):
    """Create the pyomo variables used by D-EXPANSE.

    Args:
        mod (pyo.ConcreteModel): pyomo model to configure.
    """
    # Generator power output [GW]h
    mod.p = pyo.Var(mod.DxpTechs, mod.Years, mod.DxpDays, mod.DxpHours, domain=pyo.NonNegativeReals)
    # Generator installed capacity [GW]
    mod.p_nom = pyo.Var(mod.DxpTechs, mod.Years, domain=pyo.NonNegativeReals)
    # Generator newly installed capacity [GW]
    mod.p_nom_new = pyo.Var(mod.DxpTechs, mod.Years, domain=pyo.NonNegativeReals)
    # Generator closed capacity [GW]
    mod.p_nom_closed = pyo.Var(mod.DxpTechs, mod.Years, domain=pyo.NonNegativeReals)

    # Import / Export power output
    mod.imp_p = pyo.Var(["Import"], mod.Years, mod.DxpDays, mod.DxpHours, domain=pyo.NonNegativeReals)
    mod.exp_p = pyo.Var(["Export"], mod.Years, mod.DxpDays, mod.DxpHours, domain=pyo.NonNegativeReals)
    # Import / Export installed capacity [GW]
    mod.imp_p_nom = pyo.Var(["Import"], mod.Years, domain=pyo.NonNegativeReals)
    mod.exp_p_nom = pyo.Var(["Export"], mod.Years, domain=pyo.NonNegativeReals)

    # Import / Export newly installed capacity [GW]
    mod.line_p_nom_new = pyo.Var(["Line"], mod.Years, domain=pyo.NonNegativeReals)
    # Pseudo-line power flow [GW]h
    mod.line_p = pyo.Var(["Line"], mod.Years, mod.DxpDays, mod.DxpHours, domain=pyo.Reals)
    # Pseudo-line installed capacity [GW]h
    mod.line_p_nom = pyo.Var(["Line"], mod.Years, domain=pyo.NonNegativeReals)


def cnf_model_constraints(mod: pyo.ConcreteModel, tech_df: pd.DataFrame, country_df: pd.DataFrame):
    """Set constraints.

    Args:
        mod (pyo.ConcreteModel): pyomo model
        tech_df (pd.DataFrame): dataframe with technology parameters
        country_df (pd.DataFrame): dataframe with country parameters
    """
    y_0 = mod.Years.first()
    pot_inst = tech_df.loc["Potential_installed"].fillna(value=10000).to_dict()
    # Import / Export power flow constraint
    mod.line_p_upper = pyo.ConstraintList()
    mod.line_p_lower = pyo.ConstraintList()
    for y in mod.Years:  # Add upper/lower constraint for every snapshot
        for d in mod.DxpDays:
            for h in mod.DxpHours:
                mod.line_p_upper.add(expr=mod.line_p["Line", y, d, h] <= mod.line_p_nom["Line", y])
                mod.line_p_lower.add(expr=mod.line_p["Line", y, d, h] >= -mod.line_p_nom["Line", y])
    # Import and export capacity constraint
    for y in mod.Years:
        mod.line_p_nom["Line", y].setub(pot_inst["Import"][y])
        mod.imp_p_nom["Import", y].setub(pot_inst["Import"][y])
        mod.exp_p_nom["Export", y].setub(pot_inst["Import"][y])

    # Installed capacity of import and export are the same
    mod.i_e_cons = pyo.ConstraintList()
    for y in mod.Years:
        # Import = export capacity constraint
        mod.i_e_cons.add(expr=mod.exp_p_nom["Export", y] == mod.imp_p_nom["Import", y])
        # Import <= pseudo-line capacity constraint
        mod.i_e_cons.add(expr=mod.imp_p_nom["Import", y] <= mod.line_p_nom["Line", y])

    # Import/Export power constraint
    mod.i_cons = pyo.ConstraintList()
    mod.e_cons = pyo.ConstraintList()
    for y in mod.Years:
        for d in mod.DxpDays:
            for h in mod.DxpHours:
                mod.i_cons.add(expr=mod.imp_p["Import", y, d, h] <= mod.imp_p_nom["Import", y])
                mod.e_cons.add(expr=mod.exp_p["Export", y, d, h] <= mod.exp_p_nom["Export", y])

    # Import - export - Pseudo-line flow = 0
    # create constraint list for nodal power balances
    mod.n2 = pyo.ConstraintList()
    for y in mod.Years.ordered_data()[1:]:
        for d in mod.DxpDays:
            for h in mod.DxpHours:
                # Nodal balance
                mod.n2.add(
                    expr=mod.imp_p["Import", y, d, h]
                    - mod.exp_p["Export", y, d, h]
                    - mod.line_p["Line", y, d, h]
                    == 0
                )
                # Line capacity
                mod.n2.add(
                    expr=mod.imp_p["Import", y, d, h] + mod.exp_p["Export", y, d, h]
                    <= mod.line_p_nom["Line", y]
                )

    # Actual demand
    elec_demand = (
        country_df.loc["ElSupplied_annual_central"]["Value"]
        - tech_df.loc["Actual_generation", "Storage"]
        - country_df.loc["Distribution_losses"]["Value"]
    )
    # Ratio and demand shape obtained via k-means clustering
    k_ratio_y_d, demand_y_d_h = k_means.get_demand_shape(mod.Years, mod.DxpDays, elec_demand)
    # Ratio of electricity supplied in the first year (to make load curves fit actual demand)
    elec_supplied_ratio_y0 = k_means.get_supplied_ratio_y_d(demand_y_d_h, k_ratio_y_d, mod.DxpDays, y_0)

    # Generation balance for the initial year
    # define the annual generation for each technology
    gen_y0 = tech_df.loc["Actual_generation"].loc[y_0]
    imp_y0 = country_df.loc["Actual_import"].loc[y_0, "Value"]
    exp_y0 = country_df.loc["Actual_export"].loc[y_0, "Value"]
    mod.init_p_cons = pyo.ConstraintList()
    # All generation technologies
    for c in mod.DxpTechs:
        for d in mod.DxpDays:
            mod.init_p_cons.add(
                expr=sum(mod.p[c, y_0, d, t] for t in mod.DxpHours)
                == gen_y0[c] * 1000 * elec_supplied_ratio_y0[d] / (365 * k_ratio_y_d[y_0][d])
            )
    # All Imports/Exports
    for d in mod.DxpDays:
        mod.init_p_cons.add(
            expr=sum(mod.imp_p["Import", y_0, d, t] for t in mod.DxpHours)
            == imp_y0 * 1000 * elec_supplied_ratio_y0[d] / (365 * k_ratio_y_d[y_0][d])
        )
        mod.init_p_cons.add(
            expr=sum(mod.exp_p["Export", y_0, d, t] for t in mod.DxpHours)
            == exp_y0 * 1000 * elec_supplied_ratio_y0[d] / (365 * k_ratio_y_d[y_0][d])
        )

    # Capacity in the initial year
    # In the first year the newly installed and closed capacity should be zero
    mod.init_p_nom_cons = pyo.ConstraintList()
    mod.init_line_p_nom_cons = pyo.ConstraintList()
    cap_y0 = tech_df.loc["Actual_capacity"].loc[y_0]
    for c in mod.DxpTechs:
        mod.init_p_nom_cons.add(expr=mod.p_nom[c, y_0] == cap_y0[c])
        mod.init_p_nom_cons.add(expr=mod.p_nom_new[c, y_0] == 0)
        mod.init_p_nom_cons.add(expr=mod.p_nom_closed[c, y_0] == 0)

    mod.init_line_p_nom_cons.add(expr=mod.line_p_nom["Line", y_0] == cap_y0["Import"])
    mod.init_line_p_nom_cons.add(expr=mod.line_p_nom_new["Line", y_0] == 0)

    # Demand and supply balance constraint:
    # Supplied electricity=produced electricity-electricity for own use-storage electricity use, but
    # storage does not supply anything from the second year because the initial year data is given.
    # (Generators + Pseudo-line flow) * (1 - own use) = Demand
    # TODO: demand formulation should be endogenous?
    # TODO: transmission losses could be a parameter calculation or a constant
    mod.dem_cons = pyo.ConstraintList()
    own_use = tech_df.loc["Own_use"].to_dict()
    distribution_losses = country_df.loc["Distribution_losses"]["Value"]
    trans_loss = np.round(distribution_losses / elec_demand, 3)
    for y in mod.Years:
        for d in mod.DxpDays:
            for h in mod.DxpHours:
                dem_bal_expr = prod_after_losses_y(mod, y, d, h, own_use)
                dem_bal_expr = dem_bal_expr + mod.line_p["Line", y, d, h] * (1 - own_use["Import"][y])
                mod.dem_cons.add(expr=dem_bal_expr == (demand_y_d_h[y][d][h]) * (1 + trans_loss[y]))

    # Capacity retirement due to lifetime and retirement of the initial capacity:
    # Total closed in year N - Retired initial capacity (Retirement rate*Total capacity for initial year)
    # - Total newly installed in year (N-lifetime) = 0
    mod.retirement_cons = pyo.ConstraintList()
    lifetime = tech_df.loc["Lifetime"].to_dict()
    ini_ret_cap = tech_df.loc["Initial_retired_capacity"].fillna(value=0).to_dict()
    for c in mod.DxpTechs:
        for y in mod.Years.ordered_data()[1:]:
            # Capacity that is closed due to retirement.
            # It is equal to installed capacity in the year that this capacity was installed.
            # But this should not be applicable to the initial year as it is already accounted for.
            if lifetime[c][y] <= y - y_0:
                mod.retirement_cons.add(
                    expr=mod.p_nom_closed[c, y] == ini_ret_cap[c][y] + mod.p_nom_new[c, y - lifetime[c][y]]
                )
            # Retirement of initial capacity,
            # equal to installed capacity in the initial year
            else:
                mod.retirement_cons.add(expr=mod.p_nom_closed[c, y] == ini_ret_cap[c][y])

    # Capacity transfer: balance between the capacity the year before, new capacity and closed capacity
    mod.capacity_transfer_cons = pyo.ConstraintList()
    mod.capacity_transfer_line_cons = pyo.ConstraintList()

    for c in mod.DxpTechs:
        for y in mod.Years.ordered_data()[1:]:
            mod.capacity_transfer_cons.add(
                expr=mod.p_nom[c, y] == mod.p_nom[c, y - 1] + mod.p_nom_new[c, y] - mod.p_nom_closed[c, y]
            )

    for y in mod.Years.ordered_data()[1:]:
        mod.capacity_transfer_line_cons.add(
            expr=mod.line_p_nom["Line", y] == mod.line_p_nom["Line", y - 1] + mod.line_p_nom_new["Line", y]
        )

    # Generator power output constraint: the capacity of each technology at each time step should not
    # exceed the installed capacity times the maximum load factor.
    mod.p_cons = pyo.ConstraintList()
    mod.line_p_cons = pyo.ConstraintList()
    cf_vre = get_cf_variable_renewables()
    lf_max = tech_df.loc["LF_max"].to_dict()  # TODO why are load factors above 1 for initial years?
    lf_min = tech_df.loc["LF_min"].to_dict()
    # for every flexible generator p(t) < p_nom * LF_max
    for c in mod.DxpTechs:
        for y in mod.Years:
            for d in mod.DxpDays:
                for h in mod.DxpHours:
                    if c in ["PV", "OnshoreWind", "OffshoreWind"]:
                        mod.p_cons.add(expr=mod.p[c, y, d, h] <= mod.p_nom[c, y] * cf_vre[c][y, h])
                        mod.p_cons.add(expr=mod.p[c, y, d, h] >= 0)
                    else:
                        mod.p_cons.add(expr=mod.p[c, y, d, h] <= mod.p_nom[c, y] * lf_max[c][y])
                        mod.p_cons.add(expr=mod.p[c, y, d, h] >= mod.p_nom[c, y] * lf_min[c][y])

    for y in mod.Years:
        for d in mod.DxpDays:
            for h in mod.DxpHours:
                mod.line_p_cons.add(
                    expr=mod.imp_p["Import", y, d, h] <= mod.imp_p_nom["Import", y] * lf_max["Import"][y]
                )
                mod.line_p_cons.add(
                    expr=mod.imp_p["Import", y, d, h] >= mod.imp_p_nom["Import", y] * lf_min["Import"][y]
                )
                mod.line_p_cons.add(
                    expr=mod.exp_p["Export", y, d, h] <= mod.exp_p_nom["Export", y] * lf_max["Import"][y]
                )
                mod.line_p_cons.add(
                    expr=mod.exp_p["Export", y, d, h] >= mod.exp_p_nom["Export", y] * lf_min["Import"][y]
                )

    # Generator ramp rate constraint: the capacity of each technology at each time step should not exceed
    # the installed capacity times the maximum load factor.
    mod.p_ramp_cons = pyo.ConstraintList()
    ramp_rate = tech_df.loc["Ramp_rate"].fillna(value=1).to_dict()
    for c in mod.DxpTechs:
        for y in mod.Years:
            for d in mod.DxpDays:
                for h in mod.DxpHours.ordered_data()[1:]:
                    mod.p_ramp_cons.add(
                        expr=mod.p[c, y, d, h] - mod.p[c, y, d, h - 1] <= ramp_rate[c][y] * mod.p_nom[c, y]
                    )
                    mod.p_ramp_cons.add(
                        expr=mod.p[c, y, d, h - 1] - mod.p[c, y, d, h] <= ramp_rate[c][y] * mod.p_nom[c, y]
                    )

    # Generator installed capacity constraint: set upper bounds for installed capacity
    for c in mod.DxpTechs:
        for y in mod.Years.ordered_data()[1:]:
            mod.p_nom[c, y].setub(pot_inst[c][y])

    # The peak electricity demand should be met, accounting for technology contribution to peak equation
    # TODO: Peak Demand should be a pre-set parameter, maybe?????
    # TODO: why is year zero omitted from all capacity constraints???
    mod.p_nom_peak_cons = pyo.ConstraintList()
    peak_ctrl = tech_df.loc["Peak_contr"].to_dict()
    peak_dem = country_df.loc["PeakDem_fromzero_central"]["Value"]
    for y in mod.Years.ordered_data()[1:]:
        mod.p_nom_peak_cons.add(
            expr=sum(mod.p_nom[c, y] * (1 - own_use[c][y]) * peak_ctrl[c][y] for c in mod.DxpTechs)
            >= peak_dem[y]
        )

    # The peak electricity demand, plus capacity margin, should be met
    # TODO: this constraint is more stringent than the previous one. Delete previous.
    mod.p_nom_r_cons = pyo.ConstraintList()
    cap_margin = country_df.loc["Capacity_margin"]["Value"]
    for y in mod.Years.ordered_data()[1:]:
        mod.p_nom_r_cons.add(
            expr=sum(mod.p_nom[c, y] * (1 - own_use[c][y]) * peak_ctrl[c][y] for c in mod.DxpTechs)
            >= (1 + cap_margin[y]) * peak_dem[y]
        )

    # The base load should be met, i.e. the installed capacity times the minimum load factor should be
    # lower than the base load
    # TODO: same as peak load. How to handle this if demand is an ESD?
    # TODO: what is line capacity doing in this formulation?
    mod.p_nom_base_cons = pyo.ConstraintList()
    base_dem = country_df.loc["BaseDem_central"]["Value"]
    for y in mod.Years.ordered_data()[1:]:
        mod.p_nom_base_cons.add(
            expr=sum(mod.p_nom[c, y] * (1 - own_use[c][y]) * lf_min[c][y] for c in mod.DxpTechs)
            - mod.line_p_nom["Line", y]
            <= base_dem[y]
        )

    # Build rates: the newly installed capacity every time slice should not exceed the maximum
    # technology-specific build rates
    mod.p_nom_new_cons = pyo.ConstraintList()
    mod.line_p_nom_new_cons = pyo.ConstraintList()
    build_rates = tech_df.loc["Buildrates"].to_dict()
    for c in mod.DxpTechs:
        for y in mod.Years.ordered_data()[1:]:
            mod.p_nom_new_cons.add(expr=mod.p_nom_new[c, y] <= build_rates[c][y])

    for y in mod.Years.ordered_data()[1:]:
        mod.line_p_nom_new_cons.add(expr=mod.line_p_nom_new["Line", y] <= build_rates["Import"][y])

    # Maximum potential in terms of annual electricity generation
    mod.p_potential_g_cons = pyo.ConstraintList()
    potential_annual = tech_df.loc["Potential_annual"].fillna(value=10000).to_dict()
    for c in mod.DxpTechs:
        for y in mod.Years.ordered_data()[1:]:
            mod.p_potential_g_cons.add(
                expr=sum(
                    mod.p[c, y, d, t] / 1000 * 365 * k_ratio_y_d[y][d]
                    for t in mod.DxpHours
                    for d in mod.DxpDays
                )
                <= potential_annual[c][y]
            )

    # Maximum potential in terms annual import/export line transfers
    mod.line_p_potential_g_cons = pyo.ConstraintList()
    actual_gen = tech_df.loc["Actual_generation"]
    domestic_nep = country_df.loc["ElSupplied_annual_central"]["Value"] - actual_gen.loc[:, "Import"]
    max_hist_exch = np.abs(actual_gen.loc[:, "Import"] / domestic_nep).max()
    for y in mod.Years.ordered_data()[1:]:
        mod.line_p_potential_g_cons.add(
            expr=(
                sum(
                    mod.line_p["Line", y, d, h] / 1000 * 365 * k_ratio_y_d[y][d]
                    for d in mod.DxpDays
                    for h in mod.DxpHours
                )
            )
            <= max_hist_exch * domestic_nep[y]
        )

        mod.line_p_potential_g_cons.add(
            expr=sum(
                mod.line_p["Line", y, d, h] / 1000 * 365 * k_ratio_y_d[y][d]
                for d in mod.DxpDays
                for h in mod.DxpHours
            )
            >= -max_hist_exch * domestic_nep[y]
        )


def cnf_model_objective(mod: pyo.ConcreteModel, tech_df: pd.DataFrame, country_df: pd.DataFrame):
    """Get cost expression, by first adding generic costs and then adding configuration dependent costs.

    Args:
        model (pyo.ConcreteModel): pyomo model to configure
    """
    # Generic discounted cost objective function
    # Total cost = Investment cost [currency/GW] + Fixed O&M cost [currency/(GW*year)]
    #              + Variable O&M cost [currency/TWh, efficiency not accounted]
    #              + Fuel cost [currency/TWh of fuel] + Import cost [currency/TWh]
    #              - Export revenue [currency/TWh] - Heat revenue [currency/TWh]

    # Build cost expression
    cap_cost = tech_df.loc["Inv"].to_dict()
    tot_inv_cost = sum(
        mod.p_DiscFactors[y] * mod.p_nom_new[c, y] * cap_cost[c][y] for c in mod.DxpTechs for y in mod.Years
    )
    tot_inv_cost += sum(
        mod.p_DiscFactors[y] * mod.line_p_nom_new["Line", y] * cap_cost["Import"][y] for y in mod.Years
    )

    fix_cost = tech_df.loc["Fixed_OM_annual"].to_dict()

    tot_fixed_om_cost = sum(
        mod.p_DiscFactors[y] * mod.p_nom[c, y] * fix_cost[c][y] for c in mod.DxpTechs for y in mod.Years
    )
    tot_fixed_om_cost += sum(
        mod.p_DiscFactors[y] * mod.line_p_nom["Line", y] * fix_cost["Import"][y] for y in mod.Years
    )

    # Ratio and demand shape obtained via k-means clustering
    # TODO: this should be removed from the model, day ratios should be pre-established
    elec_demand = (
        country_df.loc["ElSupplied_annual_central"]["Value"]
        - tech_df.loc["Actual_generation", "Storage"]
        - country_df.loc["Distribution_losses"]["Value"]
    )
    k_ratio_y_d, _ = k_means.get_demand_shape(mod.Years, mod.DxpDays, elec_demand)

    var_cost = tech_df.loc["Variable_OM"].to_dict()
    tot_var_om_cost = sum(
        mod.p_DiscFactors[y] * mod.p[c, y, d, h] * var_cost[c][y] / 1000 * (365 * k_ratio_y_d[y][d])
        for c in mod.DxpTechs
        for y in mod.Years
        for d in mod.DxpDays
        for h in mod.DxpHours
    )
    tot_var_om_cost += sum(
        mod.p_DiscFactors[y]
        * mod.imp_p["Import", y, d, h]
        * var_cost["Import"][y]
        / 1000
        * 365
        * k_ratio_y_d[y][d]
        for y in mod.Years
        for d in mod.DxpDays
        for h in mod.DxpHours
    )

    fuel_eff = tech_df.loc["Fuel_efficiency"].to_dict()
    fuel_cost = tech_df.loc["Fuel_cost_fuel"].to_dict()

    tot_fuel_cost = sum(
        mod.p_DiscFactors[y]
        * mod.p[c, y, d, h]
        * fuel_cost[c][y]
        / fuel_eff[c][y]
        / 1000
        * (365 * k_ratio_y_d[y][d])
        for c in mod.DxpTechs
        for y in mod.Years
        for d in mod.DxpDays
        for h in mod.DxpHours
    )

    tot_imp_cost = sum(
        mod.p_DiscFactors[y]
        * mod.imp_p["Import", y, d, h]
        * fuel_cost["Import"][y]
        / fuel_eff["Import"][y]
        / 1000
        * (365 * k_ratio_y_d[y][d])
        for y in mod.Years
        for d in mod.DxpDays
        for h in mod.DxpHours
    )

    exp_profit = country_df.loc[("Export_profit", "Value")].to_dict()
    tot_exp_revenue = sum(
        mod.p_DiscFactors[y]
        * mod.exp_p["Export", y, d, h]
        * (-exp_profit[y])
        / fuel_eff["Import"][y]
        / 1000
        * (365 * k_ratio_y_d[y][d])
        for y in mod.Years
        for d in mod.DxpDays
        for h in mod.DxpHours
    )

    heat_2_elec = tech_df.loc["Heat_to_electricity"].to_dict()
    heat_revenue = country_df.loc[("Heat_revenue", "Value")].to_dict()  # Same revenue for all techs
    total_heat_revenue = sum(
        mod.p_DiscFactors[y]
        * mod.p[c, y, d, h]
        * heat_2_elec[c][y]
        * (-heat_revenue[y])
        / 1000
        * (365 * k_ratio_y_d[y][d])
        for c in mod.DxpTechs
        for y in mod.Years
        for d in mod.DxpDays
        for h in mod.DxpHours
    )

    tot_cost_expr = tot_inv_cost + tot_fixed_om_cost + tot_var_om_cost + tot_fuel_cost + tot_imp_cost
    tot_cost_expr += tot_exp_revenue + total_heat_revenue

    # Assign model cost objective
    mod.cost = pyo.Objective(expr=tot_cost_expr, sense=pyo.minimize)
    # Instantiate the dual problem
    mod.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)


def prod_after_losses_y(mod: pyo.ConcreteModel, y, d, h, own_use: dict):
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
