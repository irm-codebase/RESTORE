# --------------------------------------------------------------------------- #
# Filename: generic_expressions.py
# Created Date: Tuesday, May 16th 2023, 5:39:39 pm
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""
Holds standard expressions that can be re-used by the model.

Rules:
- Variables: only use generics (a, ctot, cnew, fin, fout).
- Sets: only use generics (FiE, FoE).
- Do not create new parameters, variables, sets, etc.
"""
import pyomo.environ as pyo

from model_utils.configuration import DATA


# --------------------------------------------------------------------------- #
# Activity expressions
# --------------------------------------------------------------------------- #
def e_total_annual_inflow(model: pyo.ConcreteModel, f: str, e: str, y: int):
    """Total of a specific inflow/input of an entity, for each year."""
    return sum(model.DL[y, d] * sum(model.HL * model.fin[f, e, y, d, h] for h in model.H) for d in model.D)


def e_total_annual_outflow(model: pyo.ConcreteModel, f: str, e: str, y: int):
    """Total of a specific outflow/output of an entity, for each year."""
    return sum(model.DL[y, d] * sum(model.HL * model.fout[f, e, y, d, h] for h in model.H) for d in model.D)


# --------------------------------------------------------------------------- #
# Activity expressions
# --------------------------------------------------------------------------- #
def e_hourly_capacity_to_activity(_, e: str, y: int):
    """Return the maximum generation capacity of a entity for a modelled time-slice."""
    if DATA.check_cnf(e, "enable_capacity"):
        return DATA.get(e, "capacity_to_activity", y) / (365 * 24)
    return pyo.Expression.Skip


def e_total_annual_activity(model: pyo.ConcreteModel, e: str, y: int):
    """Return the total annual activity of an entity in a year."""
    return sum(model.DL[y, d] * sum(model.HL * model.a[e, y, d, h] for h in model.H) for d in model.D)


# --------------------------------------------------------------------------- #
# Cost expressions
# --------------------------------------------------------------------------- #
def e_cost_investment(model: pyo.ConcreteModel, e: str):
    """Return the total investment cost of an entity. Assumes investments occur at the start of a year slice."""
    if e not in model.Caps:
        return 0
    return sum(model.DISC[y] * DATA.get(e, "cost_investment", y) * model.cnew[e, y] for y in model.Y)


def e_cost_fixed_om(model: pyo.ConcreteModel, e: str):
    """Return the total fixed operation and maintenance cost of an entity."""
    if e not in model.Caps:
        return 0
    # For non-modelled years: assume total capacity remains the same as the last modelled year
    cost_fixed_om = sum(
        model.DISC[y + i] * DATA.get(e, "cost_fixed_om_annual", y) * model.ctot[e, y]
        for y in model.Y if y != model.Y.last()
        for i in range(model.YL())
    )
    # Add the cost of the last year
    y = model.Y.last()
    cost_fixed_om += model.DISC[y] * DATA.get(e, "cost_fixed_om_annual", y) * model.ctot[e, y]
    return cost_fixed_om


def e_cost_variable_om(model: pyo.ConcreteModel, e: str):
    """Return the total variable cost of an entity."""
    # For non-modelled years: assume activity remains the same as the last modelled year
    cost_var_om = sum(
        model.DISC[y + i] * DATA.get(e, "cost_variable_om", y) * model.e_TotalAnnualActivity[e, y]
        for y in model.Y if y != model.Y.last()
        for i in range(model.YL())
    )
    # Add the cost of the last year
    y_last = model.Y.last()
    cost_var_om += model.DISC[y_last] * DATA.get(e, "cost_variable_om", y_last) * model.e_TotalAnnualActivity[e, y_last]
    return cost_var_om
