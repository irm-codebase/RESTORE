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
Each trade element can be configured in 3 ways:
- Import mode (only enable_import set)
- Export mode (only enable_export set)
- Import/Export mode (both enable_import and enable_export set)

Capacity is shared between both aimp and aexp variables.
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic as gen

GROUP_ID = "trd_"


# --------------------------------------------------------------------------- #
# Sector-specific constraints
# --------------------------------------------------------------------------- #
def _c_activity_setup(model, element_id, y, h):
    """Ensure generic and trade-specific activity variables match the model setup.

    For trade, the total activity is equal to the sum of imports and exports.
    """
    if not cnf.DATA.check_cnf(element_id, "enable_import"):
        model.aimp[element_id, y, h].fix(True)
        model.aimp[element_id, y, h].set_value(0)
    if not cnf.DATA.check_cnf(element_id, "enable_export"):
        model.aexp[element_id, y, h].fix(True)
        model.aexp[element_id, y, h].set_value(0)
    return model.a[element_id, y, h] == model.aimp[element_id, y, h] + model.aexp[element_id, y, h]


def _c_flow_in(model: pyo.ConcreteModel, element_id: str, y: str, h: str):
    """Balance element inflows to its activity."""
    return model.aexp[element_id, y, h] == sum(
        model.fin[f, e, y, h] * cnf.DATA.get_const_fxe(e, "input_efficiency", f)
        for (f, e) in model.FiE
        if e == element_id
    )


def _c_flow_out(model: pyo.ConcreteModel, element_id: str, y: int, h: int):
    """Balance element outflows to its activity."""
    return model.aimp[element_id, y, h] == sum(
        model.fout[f, e, y, h] / cnf.DATA.get_const_fxe(e, "output_efficiency", f)
        for (f, e) in model.FoE
        if e == element_id
    )


def _c_act_max_import_annual(model, element_id, y):
    """Limit maximum imports."""
    max_act_annual = cnf.DATA.get_const(element_id, "max_activity_annual")
    if element_id not in model.TradesImp or max_act_annual is None:
        return pyo.Constraint.Skip
    return model.TPERIOD * sum(model.aimp[element_id, y, h] for h in model.Hours) <= max_act_annual


def _c_act_max_export_annual(model, element_id, y):
    """Limit maximum exports."""
    max_act_annual = cnf.DATA.get_const(element_id, "max_activity_annual")
    if element_id not in model.TradesExp or max_act_annual is None:
        return pyo.Constraint.Skip
    return model.TPERIOD * sum(model.aexp[element_id, y, h] for h in model.Hours) <= max_act_annual


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    trades = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith(GROUP_ID)])
    model.Trades = pyo.Set(initialize=trades, ordered=False)
    model.TradesImp = pyo.Set(initialize=cnf.DATA.build_cnf_set(trades, "enable_import"), ordered=False)
    model.TradesExp = pyo.Set(initialize=cnf.DATA.build_cnf_set(trades, "enable_export"), ordered=False)
    model.TradesFoE = pyo.Set(
        within=model.Flows * model.Elems,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in trades},
    )
    model.TradesFiE = pyo.Set(
        within=model.Flows * model.Elems,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in trades},
    )


def _variables(model: pyo.ConcreteModel):
    """Create any internal variables that differ from standard settings."""
    model.aimp = pyo.Var(model.Trades, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)
    model.aexp = pyo.Var(model.Trades, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Input/output
    model.trd_c_flow_in = pyo.Constraint(model.Trades, model.YOpt, model.Hours, rule=_c_flow_in)
    model.trd_c_flow_out = pyo.Constraint(model.Trades, model.YOpt, model.Hours, rule=_c_flow_out)
    model.trd_c_flow_in_max_share = pyo.Constraint(
        model.TradesFiE, model.Years, model.Hours, rule=gen.c_flow_in_max_share
    )
    model.trd_c_flow_out_max_share = pyo.Constraint(
        model.TradesFoE, model.Years, model.Hours, rule=gen.c_flow_out_max_share
    )
    # Capacity, no retirements
    model.trd_c_cap_max_annual = pyo.Constraint(model.Trades, model.Years, rule=gen.c_cap_max_annual)
    model.trd_c_cap_transfer = pyo.Constraint(model.Trades, model.YOpt, rule=gen.c_cap_transfer)
    model.trd_c_cap_buildrate = pyo.Constraint(model.Trades, model.Years, rule=gen.c_cap_buildrate)
    # Activity
    # TODO: perhaps limit annually?
    model.trd_c_act_setup = pyo.Constraint(model.Trades, model.Years, model.Hours, rule=_c_activity_setup)
    model.trd_c_act_max_imp_annual = pyo.Constraint(model.Trades, model.Years, rule=_c_act_max_import_annual)
    model.trd_c_act_max_exp_annual = pyo.Constraint(model.Trades, model.Years, rule=_c_act_max_export_annual)
    model.trd_c_act_cf_min_hour = pyo.Constraint(
        model.Trades, model.Years, model.Hours, rule=gen.c_act_cf_min_hour
    )
    model.trd_c_act_cf_max_hour = pyo.Constraint(
        model.Trades, model.Years, model.Hours, rule=gen.c_act_cf_max_hour
    )


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    # Capacity
    gen.init_capacity(model, model.Trades)
    # Activity: Import and export
    y_0 = model.Years.first()
    for element_id in model.Trades:
        if element_id in model.TradesImp:
            actimp_y0 = cnf.DATA.get_annual(element_id, "actual_import", model.Years.first())
            actimp_y0_h = actimp_y0 / (365 * 24)
            for h in model.Hours:
                model.aimp[element_id, y_0, h].fix(True)
                model.aimp[element_id, y_0, h].set_value(actimp_y0_h)
        if element_id in model.TradesExp:
            actexp_y0 = cnf.DATA.get_annual(element_id, "actual_export", model.Years.first())
            actexp_y0_h = actexp_y0 / (365 * 24)
            for h in model.Hours:
                model.aexp[element_id, y_0, h].fix(True)
                model.aexp[element_id, y_0, h].set_value(actexp_y0_h)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def _cost_variable_om(model: pyo.ConcreteModel, years):
    """Get import cost."""
    cost = sum(
        model.DR[y] * cnf.DATA.get_annual(e, "cost_import", y) * sum(model.aimp[e, y, h] for h in model.Hours)
        for e in model.TradesImp
        for y in years
    )
    cost -= sum(
        model.DR[y]
        * cnf.DATA.get_annual(e, "revenue_export", y)
        * sum(model.aexp[e, y, h] for h in model.Hours)
        for e in model.TradesExp
        for y in years
    )
    return cost


def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    cost = gen.cost_fixed_om(model, model.Trades, model.Years)
    cost += gen.cost_investment(model, model.Trades, model.Years)
    cost += _cost_variable_om(model, model.Years)
    return cost


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _variables(model)
    _constraints(model)
    _initialise(model)
