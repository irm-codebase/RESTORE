# --------------------------------------------------------------------------- #
# Filename: trade.py
# Path: /trade.py
# Created Date: Monday, March 13th 2023, 10:10:33 am
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Trade sector.

Uses unique activity variables (aimp, aexp).
Each trade entity can be configured in 3 ways:
- Import mode (only enable_import set)
- Export mode (only enable_export set)
- Import/Export mode (both enable_import and enable_export set)

Capacity is shared between both aimp and aexp variables.
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic_constraints as gen_con

GROUP_ID = "trd_"


# --------------------------------------------------------------------------- #
# Sector-specific expressions
# --------------------------------------------------------------------------- #
def _e_total_annual_import(model: pyo.ConcreteModel, e: str, y: int):
    """Return the total annual activity of an entity in a year."""
    if e not in model.TradesImp:
        return pyo.Expression.Skip
    return sum(model.DL[y, d] * sum(model.aimp[e, y, d, h] for h in model.H) for d in model.D)


def _e_total_annual_export(model: pyo.ConcreteModel, e: str, y: int):
    """Return the total annual activity of an entity in a year."""
    if e not in model.TradesExp:
        return pyo.Expression.Skip
    return sum(model.DL[y, d] * sum(model.aexp[e, y, d, h] for h in model.H) for d in model.D)


def _e_cost_variable_om(model: pyo.ConcreteModel, e: str):
    """Return the total variable cost due to trade."""
    cost = 0
    if e in model.TradesImp:
        cost += sum(
            model.DISCRATE[y] * (cnf.DATA.get(e, "cost_import", y) * model.trd_e_TotalAnnualImport[e, y])
            for y in model.Y
        )
    if e in model.TradesExp:  # Export gives revenue (negative cost)
        cost -= sum(
            model.DISCRATE[y] * (cnf.DATA.get(e, "revenue_export", y) * model.trd_e_TotalAnnualExport[e, y])
            for y in model.Y
        )
    return cost


def _e_cost_total(model: pyo.ConcreteModel):
    """Calculate the total cost of Trade entities."""
    return sum(model.e_CostInv[e] + model.e_CostFixedOM[e] + model.trd_e_CostVarOM[e] for e in model.Trades)


# --------------------------------------------------------------------------- #
# Sector-specific constraints
# --------------------------------------------------------------------------- #
def _c_activity_setup(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Ensure generic and trade-specific activity variables match the model setup.

    For trade, the total activity is equal to the sum of imports and exports.
    """
    if not cnf.DATA.check_cnf(e, "enable_import"):
        model.aimp[e, y, d, h].fix(0)
    if not cnf.DATA.check_cnf(e, "enable_export"):
        model.aexp[e, y, d, h].fix(0)
    return model.a[e, y, d, h] == model.aimp[e, y, d, h] + model.aexp[e, y, d, h]


def _c_flow_in(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Balance entity inflows to its activity."""
    return model.aexp[e, y, d, h] == sum(
        model.fin[f, ex, y, d, h] * cnf.DATA.get_fxe(ex, "input_efficiency", f, y) for (f, ex) in model.FiE if ex == e
    )


def _c_flow_out(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Balance entity outflows to its activity."""
    return model.aimp[e, y, d, h] == sum(
        model.fout[f, ex, y, d, h] / cnf.DATA.get_fxe(ex, "output_efficiency", f, y) for (f, ex) in model.FoE if ex == e
    )


def _c_act_max_import_annual(model: pyo.ConcreteModel, e: str, y: int):
    """Limit maximum imports."""
    if e not in model.TradesImp:
        return pyo.Constraint.Skip
    max_act_annual = cnf.DATA.get_const(e, "max_activity_annual")
    if max_act_annual is None:
        return pyo.Constraint.Skip
    return model.trd_e_TotalAnnualImport[e, y] <= max_act_annual


def _c_act_max_export_annual(model: pyo.ConcreteModel, e: str, y: int):
    """Limit maximum exports."""
    if e not in model.TradesExp:
        return pyo.Constraint.Skip
    max_act_annual = cnf.DATA.get_const(e, "max_activity_annual")
    if max_act_annual is None:
        return pyo.Constraint.Skip
    return model.trd_e_TotalAnnualExport[e, y] <= max_act_annual


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    trades = set(cnf.ENTITIES[cnf.ENTITIES.str.startswith(GROUP_ID)])
    model.Trades = pyo.Set(initialize=trades, ordered=False)
    model.TradesImp = pyo.Set(initialize=cnf.DATA.build_cnf_set(trades, "enable_import"), ordered=False)
    model.TradesExp = pyo.Set(initialize=cnf.DATA.build_cnf_set(trades, "enable_export"), ordered=False)
    model.TradesFoE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in trades},
    )
    model.TradesFiE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in trades},
    )


def _variables(model: pyo.ConcreteModel):
    """Create any internal variables that differ from standard settings."""
    model.aimp = pyo.Var(model.Trades, model.Y, model.D, model.H, domain=pyo.NonNegativeReals, initialize=0)
    model.aexp = pyo.Var(model.Trades, model.Y, model.D, model.H, domain=pyo.NonNegativeReals, initialize=0)


def _expressions(model: pyo.ConcreteModel):
    model.trd_e_TotalAnnualImport = pyo.Expression(model.TradesImp, model.Y, rule=_e_total_annual_import)
    model.trd_e_TotalAnnualExport = pyo.Expression(model.TradesExp, model.Y, rule=_e_total_annual_export)
    model.trd_e_CostVarOM = pyo.Expression(model.Trades, rule=_e_cost_variable_om)
    model.trd_e_CostTotal = pyo.Expression(expr=_e_cost_total(model))


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Input/output
    model.trd_c_flow_in = pyo.Constraint(model.Trades, model.Y, model.D, model.H, rule=_c_flow_in)
    model.trd_c_flow_out = pyo.Constraint(model.Trades, model.Y, model.D, model.H, rule=_c_flow_out)
    model.trd_c_flow_in_share_max = pyo.Constraint(
        model.TradesFiE, model.Y, model.D, model.H, rule=gen_con.c_flow_in_share_max
    )
    model.trd_c_flow_out_share_max = pyo.Constraint(
        model.TradesFoE, model.Y, model.D, model.H, rule=gen_con.c_flow_out_share_max
    )
    # Capacity, no retirements
    model.trd_c_cap_max_annual = pyo.Constraint(model.Trades, model.Y, rule=gen_con.c_cap_max_annual)
    model.trd_c_cap_transfer = pyo.Constraint(model.Trades, model.Y, rule=gen_con.c_cap_transfer)
    model.trd_c_cap_buildrate = pyo.Constraint(model.Trades, model.Y, rule=gen_con.c_cap_buildrate)
    # Activity
    model.trd_c_act_setup = pyo.Constraint(model.Trades, model.Y, model.D, model.H, rule=_c_activity_setup)
    model.trd_c_act_cf_min_hour = pyo.Constraint(
        model.Trades, model.Y, model.D, model.H, rule=gen_con.c_act_cf_min_hour
    )
    model.trd_c_act_cf_max_hour = pyo.Constraint(
        model.Trades, model.Y, model.D, model.H, rule=gen_con.c_act_cf_max_hour
    )
    model.trd_c_act_max_imp_annual = pyo.Constraint(model.Trades, model.Y, rule=_c_act_max_import_annual)
    model.trd_c_act_max_exp_annual = pyo.Constraint(model.Trades, model.Y, rule=_c_act_max_export_annual)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""  # NOTE: activity initialisation has been deactivated.
    # Capacity
    gen_con.init_capacity(model, model.Trades)
    # # Activity: Import and export
    # y_0 = model.Y.first()
    # for entity_id in model.Trades:
    #     if entity_id in model.TradesImp:
    #         actimp_y0 = cnf.DATA.get_annual(entity_id, "actual_import", model.Y.first())
    #         actimp_y0_h = actimp_y0 / (365 * 24)
    #         for h in model.H:
    #             model.aimp[entity_id, y_0, h].fix(True)
    #             model.aimp[entity_id, y_0, h].set_value(actimp_y0_h)
    #     if entity_id in model.TradesExp:
    #         actexp_y0 = cnf.DATA.get_annual(entity_id, "actual_export", model.Y.first())
    #         actexp_y0_h = actexp_y0 / (365 * 24)
    #         for h in model.H:
    #             model.aexp[entity_id, y_0, h].fix(True)
    #             model.aexp[entity_id, y_0, h].set_value(actexp_y0_h)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _variables(model)
    _expressions(model)
    _constraints(model)
    _initialise(model)
