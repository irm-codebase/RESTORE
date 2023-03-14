# --------------------------------------------------------------------------- #
# Filename: generic.py
# Path: /generic.py
# Created Date: Thursday, March 9th 2023, 5:03:25 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""
Holds standard functions that can be re-used by sector modules.

Rules:
- Only use generic variables (a, ctot, cnew, cret, fin, fout).
- Configuration: always check enable_capacity if the function uses ctot, cnew or cret.
- Constants: always add None handling.
- Sets: only use generics (FiE, FoE).
"""
import pyomo.environ as pyo

from model_utils.configuration import DATA


# --------------------------------------------------------------------------- #
# Flow to/from element constraints
# --------------------------------------------------------------------------- #
def c_flow_in(model: pyo.ConcreteModel, element_id: str, y: str, h: str):
    """Balance element inflows to its activity."""
    return model.a[element_id, y, h] == sum(
        model.fin[f, e, y, h] * DATA.get_const_fxe(e, "input_efficiency", f)
        for (f, e) in model.FiE
        if e == element_id
    )


def c_flow_out(model: pyo.ConcreteModel, element_id: str, y: int, h: int):
    """Balance element outflows to its activity."""
    return model.a[element_id, y, h] == sum(
        model.fout[f, e, y, h] / DATA.get_const_fxe(e, "output_efficiency", f)
        for (f, e) in model.FoE
        if e == element_id
    )


def c_flow_in_max_share(model: pyo.ConcreteModel, flow_id: str, element_id: str, y: int, h: int):
    """Limit the share of an element's inflow against the total flow."""
    max_share = DATA.get_const(element_id, "flow_in_max_share")
    if max_share is not None:
        total_inflow = sum(model.fin[f, e, y, h] for (f, e) in model.FiE if f == flow_id)
        return model.fin[flow_id, element_id, y, h] <= max_share * total_inflow
    return pyo.Constraint.Skip


def c_flow_out_max_share(model: pyo.ConcreteModel, flow_id: str, element_id: str, y: int, h: int):
    """Limit the share of an element's outflow against the total flow."""
    max_share = DATA.get_const(element_id, "flow_out_max_share")
    if max_share is not None:
        total_outflow = sum(model.fout[f, e, y, h] for (f, e) in model.FoE if f == flow_id)
        return model.fout[flow_id, element_id, y, h] <= max_share * total_outflow
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Capacity constraints
# --------------------------------------------------------------------------- #
def c_cap_max_annual(model, element_id, y):
    """Limit the maximum installed capacity of an element."""
    if DATA.check_cnf(element_id, "enable_capacity"):
        cap_max = DATA.get_const(element_id, "max_capacity_annual")
        if cap_max is not None:
            return model.ctot[element_id, y] <= cap_max
    return pyo.Constraint.Skip


def c_cap_transfer(model, element_id, y):
    """Transfer installed capacity between year slices."""
    if DATA.check_cnf(element_id, "enable_capacity"):
        total_capacity = model.ctot[element_id, y - 1] + model.cnew[element_id, y] - model.cret[element_id, y]
        return model.ctot[element_id, y] == total_capacity
    return pyo.Constraint.Skip


def c_cap_retirement(model, element_id, y):
    """Retire installed capacity if configured or if the lifetime has been exceeded."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    life = DATA.get_const(element_id, "lifetime")
    if life is None:  # Instalments last indefinitely
        return model.cret[element_id, y] == 0
    cnf_retired = DATA.get_annual(element_id, "initial_retired_capacity", y)
    if life <= y - model.Years.first():
        return model.cret[element_id, y] == cnf_retired + model.cnew[element_id, y - life]
    return model.cret[element_id, y] == cnf_retired


def c_cap_buildrate(model, element_id, y):
    """Limit the speed of annual capacity increase."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    buildrate = DATA.get_const(element_id, "buildrate")
    return model.cnew[element_id, y] <= buildrate if buildrate is not None else pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Activity constraints (element-specific and flow-independent)
# --------------------------------------------------------------------------- #
def c_act_ramp_up(model, element_id, y, h):
    """Limit the hourly activity increments of an element."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    ramp_rate = DATA.get_const(element_id, "ramp_rate")
    if ramp_rate is None or ramp_rate >= 1:  # No limit and ramping at/above 1 are equivalent
        return pyo.Constraint.Skip
    cap_to_act = DATA.get_const(element_id, "capacity_to_activity")
    max_activity_change = ramp_rate * model.ctot[element_id, y] * cap_to_act
    return model.a[element_id, y, h] - model.a[element_id, y, h - 1] <= max_activity_change


def c_act_ramp_down(model, element_id, y, h):
    """Limit the hourly activity decrements of an element."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    ramp_rate = DATA.get_const(element_id, "ramp_rate")
    if ramp_rate is None or ramp_rate >= 1:  # No limit and ramping at/above 1 are equivalent
        return pyo.Constraint.Skip
    cap_to_act = DATA.get_const(element_id, "capacity_to_activity")
    max_activity_change = ramp_rate * model.ctot[element_id, y] * cap_to_act
    return model.a[element_id, y, h - 1] - model.a[element_id, y, h] <= max_activity_change


def c_act_max_annual(model, element_id, y):
    """Limit the annual activity of an element."""
    max_act_annual = DATA.get_const(element_id, "max_activity_annual")
    if max_act_annual is not None:
        return model.TPERIOD * sum(model.a[element_id, y, h] for h in model.Hours) <= max_act_annual
    return pyo.Constraint.Skip


def c_act_cf_min_hour(model, element_id, y, h):
    """Set the minimum hourly utilisation of an element's capacity."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    lf_min = DATA.get_annual(element_id, "lf_min", y)
    cap_to_act = DATA.get_const(element_id, "capacity_to_activity")
    return lf_min * model.ctot[element_id, y] * cap_to_act <= model.a[element_id, y, h]


def c_act_cf_max_hour(model, element_id, y, h):
    """Set the maximum hourly utilisation of an element's capacity."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    lf_max = DATA.get_annual(element_id, "lf_max", y)
    cap_to_act = DATA.get_const(element_id, "capacity_to_activity")
    return model.a[element_id, y, h] <= lf_max * model.ctot[element_id, y] * cap_to_act


def c_act_cf_min_year(model, element_id, y):
    """Set the minimum annual utilisation of an element's capacity."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    lf_min = DATA.get_annual(element_id, "lf_min", y)
    cap_to_act = DATA.get_const(element_id, "capacity_to_activity")
    annual_min = lf_min * 365 * 24 * model.ctot[element_id, y] * cap_to_act
    return annual_min <= model.TPERIOD * sum(model.a[element_id, y, h] for h in model.Hours)


def c_act_cf_max_year(model, element_id, y):
    """Set the maximum annual utilisation of an element's capacity."""
    if not DATA.check_cnf(element_id, "enable_capacity"):
        return pyo.Constraint.Skip
    lf_max = DATA.get_annual(element_id, "lf_max", y)
    cap_to_act = DATA.get_const(element_id, "capacity_to_activity")
    annual_max = lf_max * 365 * 24 * model.ctot[element_id, y] * cap_to_act
    return model.TPERIOD * sum(model.a[element_id, y, h] for h in model.Hours) <= annual_max


# --------------------------------------------------------------------------- #
# Initialisation
# --------------------------------------------------------------------------- #
def init_activity(model, elements):
    """Set the initial activity in a set of elements."""
    y_0 = model.Y0.first()
    for element_id in elements:
        act_y0 = DATA.get_annual(element_id, "actual_activity", y_0)
        act_y0_h = act_y0 / (365 * 24)
        for h in model.Hours:
            model.a[element_id, y_0, h].fix(True)
            model.a[element_id, y_0, h].set_value(act_y0_h)


def init_capacity(model: pyo.ConcreteModel, elements: set):
    """Set the capacity in the inital year, if enabled."""
    y_0 = model.Y0.first()  # Ensure y_0 is numeric
    for element_id in elements:
        if DATA.check_cnf(element_id, "enable_capacity"):
            cap_y0 = DATA.get_annual(element_id, "actual_capacity", y_0)
            model.ctot[element_id, y_0].fix(True)
            model.cnew[element_id, y_0].fix(True)
            model.cret[element_id, y_0].fix(True)
            model.ctot[element_id, y_0].set_value(cap_y0)
            model.cnew[element_id, y_0].set_value(0)
            model.cret[element_id, y_0].set_value(0)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def cost_investment(model: pyo.ConcreteModel, entities, years):
    """Get investment cost for a set of elements."""
    cost = 0
    for e in entities:
        if DATA.check_cnf(e, "enable_capacity"):
            cost += sum(
                model.DR[y] * DATA.get_annual(e, "cost_investment", y) * model.cnew[e, y]
                for y in years
            )
    return cost


def cost_fixed_om(model: pyo.ConcreteModel, entities, years):
    """Get fixed O&M cost for a set of elements."""
    cost = 0
    for e in entities:
        if DATA.check_cnf(e, "enable_capacity"):
            cost += sum(
                model.DR[y] * DATA.get_annual(e, "cost_fixed_om_annual", y) * model.ctot[e, y]
                for y in years
            )
    return cost


def cost_variable_om(model: pyo.ConcreteModel, entities, years):
    """Get variable O&M cost for a set of elements."""
    cost = sum(
        model.DR[y] * DATA.get_annual(e, "cost_variable_om", y) * sum(model.a[e, y, h] for h in model.Hours)
        for e in entities
        for y in years
    )
    return cost


def cost_combined(model: pyo.ConcreteModel, entities: set, years: set):
    """Wrap the most generic cost setup."""
    cost = cost_investment(model, entities, years)
    cost += cost_fixed_om(model, entities, years)
    cost += cost_variable_om(model, entities, years)
    return cost
