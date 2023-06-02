# --------------------------------------------------------------------------- #
# Filename: generic_constraints.py
# Created Date: Tuesday, May 16th 2023, 5:39:39 pm
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
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
def c_flow_in(model: pyo.ConcreteModel, entity_id: str, y: int, d: int, h: int):
    """Balance entity inflows to its activity."""
    inflows = sum(
        model.fin[f, e, y, d, h] * DATA.get_fxe(e, "input_efficiency", f, y)
        for (f, e) in model.FiE
        if e == entity_id
    )
    return inflows == model.a[entity_id, y, d, h]


def c_flow_in_share_equal(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit a specific in-flow to be equal to a share of the sum of the total in-flows in that flow."""
    share_equal = DATA.get_fxe(entity_id, "flow_in_share_equal", flow_id, y)
    if share_equal is not None:
        total_inflow = sum(model.fin[f, e, y, d, h] for (f, e) in model.FiE if f == flow_id)
        return model.fin[flow_id, entity_id, y, d, h] == share_equal * total_inflow
    return pyo.Constraint.Skip


def c_flow_in_share_max(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an in-flow to be below a share of the sum of the total in-flows in that flow."""
    share_equal = DATA.get_fxe(entity_id, "flow_in_share_max", flow_id, y)
    if share_equal is not None:
        total_inflow = sum(model.fin[f, e, y, d, h] for (f, e) in model.FiE if f == flow_id)
        return model.fin[flow_id, entity_id, y, d, h] <= share_equal * total_inflow
    return pyo.Constraint.Skip


def c_flow_in_share_min(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an in-flow to be above a share of the sum of the total in-flows in that flow."""
    share_equal = DATA.get_fxe(entity_id, "flow_in_share_min", flow_id, y)
    if share_equal is not None:
        total_inflow = sum(model.fin[f, e, y, d, h] for (f, e) in model.FiE if f == flow_id)
        return model.fin[flow_id, entity_id, y, d, h] >= share_equal * total_inflow
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Out-flow constraints (relates to flow-out-of-entity, FoE)
# --------------------------------------------------------------------------- #
def c_flow_out(model: pyo.ConcreteModel, entity_id: str, y: int, d: int, h: int):
    """Balance entity outflows to its activity."""
    outflows = sum(
        model.fout[f, e, y, d, h] / DATA.get_fxe(e, "output_efficiency", f, y)
        for (f, e) in model.FoE
        if e == entity_id
    )
    return outflows == model.a[entity_id, y, d, h]


def c_flow_out_share_equal(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an outflow to be equal to a share of the sum of all outflows."""
    share_equal = DATA.get_fxe(entity_id, "flow_out_share_equal", flow_id, y)
    if share_equal is not None:
        total_outflow = sum(model.fout[f, e, y, d, h] for (f, e) in model.FoE if f == flow_id)
        return model.fout[flow_id, entity_id, y, d, h] == share_equal * total_outflow
    return pyo.Constraint.Skip


def c_flow_out_share_max(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an outflow to be below a share of the sum of all outflows."""
    share_max = DATA.get_fxe(entity_id, "flow_out_share_max", flow_id, y)
    if share_max is not None:
        total_outflow = sum(model.fout[f, e, y, d, h] for (f, e) in model.FoE if f == flow_id)
        return model.fout[flow_id, entity_id, y, d, h] <= share_max * total_outflow
    return pyo.Constraint.Skip


def c_flow_out_share_min(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Limit an outflow to be above a share of the sum of all outflows."""
    share_min = DATA.get_fxe(entity_id, "flow_out_share_min", flow_id, y)
    if share_min is not None:
        total_outflow = sum(model.fout[f, e, y, d, h] for (f, e) in model.FoE if f == flow_id)
        return model.fout[flow_id, entity_id, y, d, h] >= share_min * total_outflow
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Input constraints
# --------------------------------------------------------------------------- #
def c_input_share_equal(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's input to be equal to a share of the sum of all inputs."""
    input_share_equal = DATA.get_fxe(entity_id, "input_share_equal", flow_id, y)
    if input_share_equal is not None:
        total_input = sum(model.fin[f, e, y, d, h] for (f, e) in model.FiE if e == entity_id)
        return model.fin[flow_id, entity_id, y, d, h] == input_share_equal * total_input
    return pyo.Constraint.Skip


def c_input_share_max(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's input to be below a maximum share of the sum of all inputs."""
    input_share_max = DATA.get_fxe(entity_id, "input_share_max", flow_id, y)
    if input_share_max is not None:
        total_input = sum(model.fin[f, e, y, d, h] for (f, e) in model.FiE if e == entity_id)
        return model.fin[flow_id, entity_id, y, d, h] <= input_share_max * total_input
    return pyo.Constraint.Skip


def c_input_share_min(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's input to be above a minimum share of the sum of all inputs."""
    input_share_min = DATA.get_fxe(entity_id, "input_share_min", flow_id, y)
    if input_share_min is not None:
        total_input = sum(model.fin[f, e, y, d, h] for (f, e) in model.FiE if e == entity_id)
        return model.fin[flow_id, entity_id, y, d, h] >= input_share_min * total_input
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Output constraints
# --------------------------------------------------------------------------- #
def c_output_share_equal(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's output to be equal to a share of the sum of all outputs."""
    output_share_equal = DATA.get_fxe(entity_id, "output_share_equal", flow_id, y)
    if output_share_equal is not None:
        total_output = sum(model.fout[f, e, y, d, h] for (f, e) in model.FoE if e == entity_id)
        return model.fout[flow_id, entity_id, y, d, h] == output_share_equal * total_output
    return pyo.Constraint.Skip


def c_output_share_max(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's output to be below a maximum share of the sum of all outputs."""
    output_share_max = DATA.get_fxe(entity_id, "output_share_max", flow_id, y)
    if output_share_max is not None:
        total_output = sum(model.fout[f, e, y, d, h] for (f, e) in model.FoE if e == entity_id)
        return model.fout[flow_id, entity_id, y, d, h] == output_share_max * total_output
    return pyo.Constraint.Skip


def c_output_share_min(model: pyo.ConcreteModel, flow_id: str, entity_id: str, y: int, d: int, h: int):
    """Constrain an entity's output to be above a minimum share of the sum of all outputs."""
    output_share_min = DATA.get_fxe(entity_id, "output_share_min", flow_id, y)
    if output_share_min is not None:
        total_output = sum(model.fout[f, e, y, d, h] for (f, e) in model.FoE if e == entity_id)
        return model.fout[flow_id, entity_id, y, d, h] == output_share_min * total_output
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Capacity constraints
# --------------------------------------------------------------------------- #
def c_cap_max_annual(model: pyo.ConcreteModel, e: str, y: int):
    """Limit the maximum installed capacity of an entity."""
    if DATA.check_cnf(e, "enable_capacity"):
        cap_max = DATA.get(e, "max_capacity_annual", y)
        if cap_max is not None:
            return model.ctot[e, y] <= cap_max
    return pyo.Constraint.Skip


def c_cap_transfer(model: pyo.ConcreteModel, e: str, y: int):
    """Transfer installed capacity between year slices."""
    if DATA.check_cnf(e, "enable_capacity"):
        initial_capacity = DATA.get_annual(e, "actual_capacity", model.Y.first())
        lifetime = DATA.get_const(e, "lifetime")

        if lifetime is None:
            # No lifetime implies added capacity lasts forever
            new_cap = sum(model.cnew[e, yx] for yx in model.Y if yx <= y)
            residual_capacity = initial_capacity
        else:
            new_cap = sum(model.cnew[e, yx] for yx in model.Y if yx <= y and y - yx < lifetime)
            if y - model.Y.first() < lifetime:
                retired = sum(DATA.get_annual(e, "initial_retired_capacity", yx) for yx in model.YALL if yx <= y)
                residual_capacity = initial_capacity - retired
            else:
                residual_capacity = 0
        return model.ctot[e, y] == residual_capacity + new_cap
    return pyo.Constraint.Skip


def c_cap_buildrate(model: pyo.ConcreteModel, e: str, y: int):
    """Limit maximum new capacity installed."""
    if DATA.check_cnf(e, "enable_capacity"):
        buildrate = DATA.get(e, "buildrate", y) * model.YL
        return model.cnew[e, y] <= buildrate if buildrate is not None else pyo.Constraint.Skip
    return pyo.Constraint.Skip


def c_cap_growthrate(model: pyo.ConcreteModel, e: str, y: int):
    """Limit the growth rate of total capacity."""
    if DATA.check_cnf(e, "enable_capacity"):
        growthrate = DATA.get(e, "growthrate", y) ** model.YL
        if growthrate is not None:
            return model.ctot[e, y] == growthrate * model.ctot[e, y - model.YL]
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Activity constraints (entity-specific and flow-independent)
# --------------------------------------------------------------------------- #
def c_act_ramp_up(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Limit the hourly activity increments of an entity."""
    if DATA.check_cnf(e, "enable_capacity"):
        ramp_rate = DATA.get(e, "ramp_rate", y) * model.HL
        if ramp_rate is None or ramp_rate >= 1:  # No limit and ramping at/above 1 are equivalent
            return pyo.Constraint.Skip
        max_activity_change = ramp_rate * model.ctot[e, y] * model.e_HourlyC2A[e, y]
        return model.a[e, y, d, h] - model.a[e, y, d, h - model.HL] <= max_activity_change
    return pyo.Constraint.Skip


def c_act_ramp_down(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Limit the hourly activity decrements of an entity."""
    if DATA.check_cnf(e, "enable_capacity"):
        ramp_rate = DATA.get(e, "ramp_rate", y) * model.HL
        if ramp_rate is None or ramp_rate >= 1:  # No limit and ramping at/above 1 are equivalent
            return pyo.Constraint.Skip
        max_activity_change = ramp_rate * model.ctot[e, y] * model.e_HourlyC2A[e, y]
        return model.a[e, y, d, h - model.HL] - model.a[e, y, d, h] <= max_activity_change
    return pyo.Constraint.Skip


def c_act_max_annual(model: pyo.ConcreteModel, e: str, y: int):
    """Limit the annual activity of an entity."""
    max_act_annual = DATA.get_const(e, "max_activity_annual")
    if max_act_annual is not None:
        return model.e_TotalAnnualActivity[e, y] <= max_act_annual
    return pyo.Constraint.Skip


def c_act_cf_min_hour(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Set the minimum hourly utilisation of an entity's capacity."""
    if DATA.check_cnf(e, "enable_capacity"):
        lf_min = DATA.get(e, "lf_min", y)
        return lf_min * model.ctot[e, y] * model.e_HourlyC2A[e, y] <= model.a[e, y, d, h]
    return pyo.Constraint.Skip


def c_act_cf_max_hour(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Set the maximum hourly utilisation of an entity's capacity."""
    if DATA.check_cnf(e, "enable_capacity"):
        lf_max = DATA.get(e, "lf_max", y)
        return model.a[e, y, d, h] <= lf_max * model.ctot[e, y] * model.e_HourlyC2A[e, y]
    return pyo.Constraint.Skip


def c_act_cf_min_year(model: pyo.ConcreteModel, e: str, y: int):
    """Set the minimum annual utilisation of an entity's capacity."""
    if DATA.check_cnf(e, "enable_capacity"):
        lf_min = DATA.get(e, "lf_min", y)
        cap_to_act = DATA.get(e, "capacity_to_activity", y)
        return lf_min * model.ctot[e, y] * cap_to_act <= model.e_TotalAnnualActivity[e, y]
    return pyo.Constraint.Skip


def c_act_cf_max_year(model: pyo.ConcreteModel, e: str, y: int):
    """Set the maximum annual utilisation of an entity's capacity."""
    if DATA.check_cnf(e, "enable_capacity"):
        lf_max = DATA.get(e, "lf_max", y)
        cap_to_act = DATA.get(e, "capacity_to_activity", y)
        return model.e_TotalAnnualActivity[e, y] <= lf_max * model.ctot[e, y] * cap_to_act
    return pyo.Constraint.Skip


# --------------------------------------------------------------------------- #
# Initialisation
# --------------------------------------------------------------------------- #
def init_activity(model, entity_list):
    """Set the initial activity in a set of entity_list."""
    hours_in_year = 365 * 24
    y_0 = model.Y0.first()
    for e in entity_list:
        act = DATA.get_annual(e, "actual_activity", y_0) / hours_in_year
        model.a[e, y_0, :, :].fix(act)


def init_capacity(model: pyo.ConcreteModel, entity_list: set):
    """Set the capacity in the inital year, if enabled."""
    y_0 = model.Y0.first()
    for entity_id in entity_list:
        if DATA.check_cnf(entity_id, "enable_capacity"):
            cap_enable = DATA.get_annual(entity_id, "actual_capacity", y_0)
            model.cnew[entity_id, y_0].fix(0)
            model.ctot[entity_id, y_0].fix(cap_enable)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def cost_investment(model: pyo.ConcreteModel, entity_list, years):
    """Get investment cost for a set of entity_list."""
    cost = 0
    for e in entity_list:
        if DATA.check_cnf(e, "enable_capacity"):
            cost += sum(model.DISC[y] * DATA.get(e, "cost_investment", y) * model.cnew[e, y] for y in years)
    return cost


def cost_fixed_om(model: pyo.ConcreteModel, entity_list, years):
    """Get fixed O&M cost for a set of entity_list."""
    cost = 0
    for e in entity_list:
        if DATA.check_cnf(e, "enable_capacity"):
            cost += sum(
                model.DISC[y] * DATA.get(e, "cost_fixed_om_annual", y) * model.ctot[e, y] for y in years
            )
    return cost


def cost_variable_om(model: pyo.ConcreteModel, entity_list, years):
    """Get variable O&M cost for a set of entity_list."""
    cost = sum(
        model.DISC[y] * DATA.get(e, "cost_variable_om", y) * sum(model.a[e, y, h] for h in model.H)
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
