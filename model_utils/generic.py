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
Holds standard constraints that can be re-used by sector modules.

Rules:
- Only use generic variables (a, ctot, cnew, cret, fin, fout).
- Configuration: always check enable_capacity if the function uses ctot, cnew or cret.
- Sets: only use generics (FiE, FoE).
"""
import pyomo.environ as pyo

from model_utils.configuration import DATA


# --------------------------------------------------------------------------- #
# In-flow constraints (relates to flow-into-entity, FiE)
# --------------------------------------------------------------------------- #
def c_flow_in(model: pyo.ConcreteModel, n: str, entity_id: str, y: int, d: int, h: int):
    """Balance entity inflows to its activity."""
    inflows = sum(
        model.fin[n, f, e, y, d, h] * DATA.get_fxe(e, "input_efficiency", f, y)
        for (f, e) in model.FiE
        if e == entity_id
    )
    return inflows == model.a[n, entity_id, y, d, h]


def c_flow_in_share_equal(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit a specific in-flow to be equal to a share of the sum of the total in-flows in that flow."""
    share_equal = DATA.get_fxe(entity_id, "flow_in_share_equal", flow_id, y)
    if share_equal is not None:
        total_inflow = sum(model.fin[n, f, e, y, d, h] for (f, e) in model.FiE if f == flow_id)
        return model.fin[n, flow_id, entity_id, y, d, h] == share_equal * total_inflow
    return pyo.Constraint.Skip


def c_flow_in_share_max(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an in-flow to be below a share of the sum of the total in-flows in that flow."""
    share_equal = DATA.get_fxe(entity_id, "flow_in_share_max", flow_id, y)
    if share_equal is not None:
        total_inflow = sum(model.fin[n, f, e, y, d, h] for (f, e) in model.FiE if f == flow_id)
        return model.fin[n, flow_id, entity_id, y, d, h] <= share_equal * total_inflow
    return pyo.Constraint.Skip


def c_flow_in_share_min(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an in-flow to be above a share of the sum of the total in-flows in that flow."""
    share_equal = DATA.get_fxe(entity_id, "flow_in_share_min", flow_id, y)
    if share_equal is not None:
        total_inflow = sum(model.fin[n, f, e, y, d, h] for (f, e) in model.FiE if f == flow_id)
        return model.fin[n, flow_id, entity_id, y, d, h] >= share_equal * total_inflow
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Out-flow constraints (relates to flow-out-of-entity, FoE)
# --------------------------------------------------------------------------- #
def c_flow_out(model: pyo.ConcreteModel, n: str, entity_id: str, y: int, d: int, h: int):
    """Balance entity outflows to its activity."""
    outflows = sum(
        model.fout[n, f, e, y, d, h] * DATA.get_fxe(e, "output_efficiency", f, y)
        for (f, e) in model.FoE
        if e == entity_id
    )
    return outflows == model.a[n, entity_id, y, d, h]


def c_flow_out_share_equal(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an outflow to be equal to a share of the sum of all outflows."""
    share_equal = DATA.get_fxe(entity_id, "flow_out_share_equal", flow_id, y)
    if share_equal is not None:
        total_outflow = sum(model.fout[n, f, e, y, d, h] for (f, e) in model.FoE if f == flow_id)
        return model.fout[n, flow_id, entity_id, y, d, h] == share_equal * total_outflow
    return pyo.Constraint.Skip


def c_flow_out_share_max(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an outflow to be below a share of the sum of all outflows."""
    share_max = DATA.get_fxe(entity_id, "flow_out_share_max", flow_id, y)
    if share_max is not None:
        total_outflow = sum(model.fout[n, f, e, y, d, h] for (f, e) in model.FoE if f == flow_id)
        return model.fout[n, flow_id, entity_id, y, d, h] <= share_max * total_outflow
    return pyo.Constraint.Skip


def c_flow_out_share_min(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an outflow to be above a share of the sum of all outflows."""
    share_min = DATA.get_fxe(entity_id, "flow_out_share_min", flow_id, y)
    if share_min is not None:
        total_outflow = sum(model.fout[n, f, e, y, d, h] for (f, e) in model.FoE if f == flow_id)
        return model.fout[n, flow_id, entity_id, y, d, h] >= share_min * total_outflow
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Input constraints
# --------------------------------------------------------------------------- #
def c_input_share_equal(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's input to be equal to a share of the sum of all inputs."""
    input_share_equal = DATA.get_fxe(entity_id, "input_share_equal", flow_id, y)
    if input_share_equal is not None:
        total_input = sum(model.fin[n, f, e, y, d, h] for (f, e) in model.FiE if e == entity_id)
        return model.fin[n, flow_id, entity_id, y, d, h] == input_share_equal * total_input
    return pyo.Constraint.Skip


def c_input_share_max(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's input to be below a maximum share of the sum of all inputs."""
    input_share_max = DATA.get_fxe(entity_id, "input_share_max", flow_id, y)
    if input_share_max is not None:
        total_input = sum(model.fin[n, f, e, y, d, h] for (f, e) in model.FiE if e == entity_id)
        return model.fin[n, flow_id, entity_id, y, d, h] <= input_share_max * total_input
    return pyo.Constraint.Skip


def c_input_share_min(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's input to be above a minimum share of the sum of all inputs."""
    input_share_min = DATA.get_fxe(entity_id, "input_share_min", flow_id, y)
    if input_share_min is not None:
        total_input = sum(model.fin[n, f, e, y, d, h] for (f, e) in model.FiE if e == entity_id)
        return model.fin[n, flow_id, entity_id, y, d, h] >= input_share_min * total_input
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Output constraints
# --------------------------------------------------------------------------- #
def c_output_share_equal(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's output to be equal to a share of the sum of all outputs."""
    output_share_equal = DATA.get_fxe(entity_id, "output_share_equal", flow_id, y)
    if output_share_equal is not None:
        total_output = sum(model.fout[n, f, e, y, d, h] for (f, e) in model.FoE if e == entity_id)
        return model.fout[n, flow_id, entity_id, y, d, h] == output_share_equal * total_output
    return pyo.Constraint.Skip


def c_output_share_max(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's output to be below a maximum share of the sum of all outputs."""
    output_share_max = DATA.get_fxe(entity_id, "output_share_max", flow_id, y)
    if output_share_max is not None:
        total_output = sum(model.fout[n, f, e, y, d, h] for (f, e) in model.FoE if e == entity_id)
        return model.fout[n, flow_id, entity_id, y, d, h] == output_share_max * total_output
    return pyo.Constraint.Skip


def c_output_share_min(model: pyo.ConcreteModel, n: str, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's output to be above a minimum share of the sum of all outputs."""
    output_share_min = DATA.get_fxe(entity_id, "output_share_min", flow_id, y)
    if output_share_min is not None:
        total_output = sum(model.fout[n, f, e, y, d, h] for (f, e) in model.FoE if e == entity_id)
        return model.fout[n, flow_id, entity_id, y, d, h] == output_share_min * total_output
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Capacity constraints
# --------------------------------------------------------------------------- #
def c_cap_max_annual(model: pyo.ConcreteModel, n: str, e: str, y: int):
    """Limit the maximum installed capacity of an entity."""
    if DATA.check_cnf(e, "enable_capacity"):
        cap_max = DATA.get(e, "max_capacity_annual", y)
        if cap_max is not None:
            return model.ctot[n, e, y] <= cap_max
    return pyo.Constraint.Skip


def c_cap_transfer(model: pyo.ConcreteModel, n: str, e: str, y: int):
    """Transfer installed capacity between year slices."""
    if DATA.check_cnf(e, "enable_capacity") and y > DATA.check_cnf(e, "enable_year"):
        total_capacity = model.ctot[n, e, y - 1] + model.cnew[n, e, y] - model.cret[n, e, y]
        return model.ctot[n, e, y] == total_capacity
    return pyo.Constraint.Skip


def c_cap_retirement(model: pyo.ConcreteModel, n: str, e: str, y: int):
    """Retire installed capacity if configured or if the lifetime has been exceeded."""
    if DATA.check_cnf(e, "enable_capacity") and y > DATA.check_cnf(e, "enable_year"):
        life = DATA.get_const(e, "lifetime")
        if life is None:  # Instalments last indefinitely
            return model.cret[n, e, y] == 0
        if life <= y - model.Y.first():
            # TODO: I feel like this approach causes double retirements... Another D-EXPANSE issue? Evaluate.
            return model.cret[n, e, y] == model.cnew[n, e, y - life]
        cnf_retired = DATA.get_annual(e, "initial_retired_capacity", y)
        return model.cret[n, e, y] == cnf_retired
    return pyo.Constraint.Skip


def c_cap_buildrate(model: pyo.ConcreteModel, n: str, e: str, y: int):
    """Limit the speed of annual capacity increase."""
    if DATA.check_cnf(e, "enable_capacity") and y > DATA.check_cnf(e, "enable_year"):
        buildrate = DATA.get(e, "buildrate", y)
        return model.cnew[n, e, y] <= buildrate if buildrate is not None else pyo.Constraint.Skip
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Activity constraints (entity-specific and flow-independent)
# --------------------------------------------------------------------------- #
def c_act_ramp_up(model: pyo.ConcreteModel, n: str, entity_id: str, y: int, d: int, h: int):
    """Limit the hourly activity increments of an entity."""
    if DATA.check_cnf(entity_id, "enable_capacity") and y > DATA.check_cnf(entity_id, "enable_year"):
        ramp_rate = DATA.get(entity_id, "ramp_rate", y)
        if ramp_rate is None or ramp_rate >= 1:  # No limit and ramping at/above 1 are equivalent
            return pyo.Constraint.Skip
        cap_to_act = DATA.get(entity_id, "capacity_to_activity", y) * model.HL / (365 * 24)
        max_activity_change = ramp_rate * model.ctot[n, entity_id, y] * cap_to_act
        return model.a[n, entity_id, y, d, h] - model.a[n, entity_id, y, d, h - 1] <= max_activity_change
    return pyo.Constraint.Skip


def c_act_ramp_down(model: pyo.ConcreteModel, n: str, entity_id: str, y: int, d: int, h: int):
    """Limit the hourly activity decrements of an entity."""
    if DATA.check_cnf(entity_id, "enable_capacity") and y > DATA.check_cnf(entity_id, "enable_year"):
        ramp_rate = DATA.get(entity_id, "ramp_rate", y)
        if ramp_rate is None or ramp_rate >= 1:  # No limit and ramping at/above 1 are equivalent
            return pyo.Constraint.Skip
        cap_to_act = DATA.get(entity_id, "capacity_to_activity", y) * model.HL / (365 * 24)
        max_activity_change = ramp_rate * model.ctot[n, entity_id, y] * cap_to_act
        return model.a[n, entity_id, y, d, h - 1] - model.a[n, entity_id, y, d, h] <= max_activity_change
    return pyo.Constraint.Skip


def c_act_max_annual(model: pyo.ConcreteModel, n: str, entity_id: str, y: int):
    """Limit the annual activity of an entity."""
    max_act_annual = DATA.get_const(entity_id, "max_activity_annual")
    if max_act_annual is not None:
        act_annual = sum(model.DL[y, d] * sum(model.a[n, entity_id, y, d, h] for h in model.H) for d in model.D)
        return act_annual <= max_act_annual
    return pyo.Constraint.Skip


def c_act_cf_min_hour(model: pyo.ConcreteModel, n: str, entity_id: str, y: int, d: int, h: int):
    """Set the minimum hourly utilisation of an entity's capacity."""
    if DATA.check_cnf(entity_id, "enable_capacity") and y > DATA.check_cnf(entity_id, "enable_year"):
        lf_min = DATA.get(entity_id, "lf_min", y)
        cap_to_act = DATA.get(entity_id, "capacity_to_activity", y) * model.HL / (365 * 24)
        return lf_min * model.ctot[n, entity_id, y] * cap_to_act <= model.a[n, entity_id, y, d, h]
    return pyo.Constraint.Skip


def c_act_cf_max_hour(model: pyo.ConcreteModel, n: str, entity_id: str, y: int, d: int, h: int):
    """Set the maximum hourly utilisation of an entity's capacity."""
    if DATA.check_cnf(entity_id, "enable_capacity") and y > DATA.check_cnf(entity_id, "enable_year"):
        lf_max = DATA.get(entity_id, "lf_max", y)
        cap_to_act = DATA.get(entity_id, "capacity_to_activity", y) * model.HL / (365 * 24)
        return model.a[n, entity_id, y, d, h] <= lf_max * model.ctot[n, entity_id, y] * cap_to_act
    return pyo.Constraint.Skip


def c_act_cf_min_year(model: pyo.ConcreteModel, n: str, entity_id: str, y: int):
    """Set the minimum annual utilisation of an entity's capacity."""
    if DATA.check_cnf(entity_id, "enable_capacity") and y > DATA.check_cnf(entity_id, "enable_year"):
        lf_min = DATA.get(entity_id, "lf_min", y)
        cap_to_act = DATA.get(entity_id, "capacity_to_activity", y)
        annual_min = lf_min * model.ctot[n, entity_id, y] * cap_to_act
        act_annual = sum(model.DL[y, d] * sum(model.a[n, entity_id, y, d, h] for h in model.H) for d in model.D)
        return annual_min <= act_annual
    return pyo.Constraint.Skip


def c_act_cf_max_year(model: pyo.ConcreteModel, n: str, entity_id: str, y: int):
    """Set the maximum annual utilisation of an entity's capacity."""
    if DATA.check_cnf(entity_id, "enable_capacity") and y > DATA.check_cnf(entity_id, "enable_year"):
        lf_max = DATA.get(entity_id, "lf_max", y)
        cap_to_act = DATA.get(entity_id, "capacity_to_activity", y)
        annual_max = lf_max * model.ctot[n, entity_id, y] * cap_to_act
        act_annual = sum(model.DL[y, d] * sum(model.a[n, entity_id, y, d, h] for h in model.H) for d in model.D)
        return act_annual <= annual_max
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Initialisation
# --------------------------------------------------------------------------- #
def init_activity(model, entity_list):
    """Set the initial activity in a set of entity_list."""
    hours_in_year = 365 * 24
    y_0 = model.Y0.first()
    for entity_id in entity_list:
        enable_year = DATA.check_cnf(entity_id, "enable_year")
        for y in model.Years:
            if y == y_0 and y == enable_year:
                # Activity should only be initialized if both y_0 and the enable year coincide.
                act = DATA.get_annual(entity_id, "actual_activity", y) / hours_in_year
            else:
                act = 0
            model.a[entity_id, y, :].fix(act)

            if y == enable_year:
                break


def init_capacity(model: pyo.ConcreteModel, entity_list: set):
    """Set the capacity in the inital year, if enabled."""
    # TODO: Think of a leaner way to implement temporal enabling/disabling.
    for entity_id in entity_list:
        if DATA.check_cnf(entity_id, "enable_capacity"):
            enable_year = DATA.check_cnf(entity_id, "enable_year")
            cap_enable = DATA.get_annual(entity_id, "actual_capacity", enable_year)
            # Capacity is zero until enabled.
            for y in model.Years:
                model.cnew[entity_id, y].fix(0)
                model.cret[entity_id, y].fix(0)
                if y == enable_year:
                    model.ctot[entity_id, y].fix(cap_enable)
                    break
                model.ctot[entity_id, y].fix(0)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def cost_investment(model: pyo.ConcreteModel, entity_list, years):
    """Get investment cost for a set of entity_list."""
    cost = 0
    for e in entity_list:
        if DATA.check_cnf(e, "enable_capacity"):
            cost += sum(model.DISCOUNT_RATE[y] * DATA.get(e, "cost_investment", y) * model.cnew[e, y] for y in years)
    return cost


def cost_fixed_om(model: pyo.ConcreteModel, entity_list, years):
    """Get fixed O&M cost for a set of entity_list."""
    cost = 0
    for e in entity_list:
        if DATA.check_cnf(e, "enable_capacity"):
            cost += sum(
                model.DISCOUNT_RATE[y] * DATA.get(e, "cost_fixed_om_annual", y) * model.ctot[e, y] for y in years
            )
    return cost


def cost_variable_om(model: pyo.ConcreteModel, entity_list, years):
    """Get variable O&M cost for a set of entity_list."""
    cost = sum(
        model.DISCOUNT_RATE[y] * DATA.get(e, "cost_variable_om", y) * sum(model.a[e, y, h] for h in model.Hours)
        for e in entity_list
        for y in years
    )
    return cost


def cost_combined(model: pyo.ConcreteModel, entity_list: set, years: set):
    """Wrap the most generic cost setup."""
    cost = cost_investment(model, entity_list, years)
    cost += cost_fixed_om(model, entity_list, years)
    cost += cost_variable_om(model, entity_list, years)
    return cost
