# --------------------------------------------------------------------------- #
# Filename: storage.py
# Created Date: Monday, May 8th 2023, 11:59:03 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Storage sector.

To reduce model complexity, the module re-purposes standard model variables as much as possible.
For clarity:
- fin equates to the storage uptake/charge/inflow
- fout equates to the storage dispatch/discharge/outflow
- a equates to the storage state-of-charge

# NOTE: no SoC operational range constraints, for now (i.e., full charge and empty states possible).
# NOTE: constraints assume capacity is ALWAYS enabled (deactivation does not make sense for this module)

The constraints are based on PyPSA's storage constraints, see:
https://pypsa.readthedocs.io/en/latest/optimal_power_flow.html#storage-unit-constraints

An option to use Kotzur's seasonal storage method will be added in the future.
https://doi.org/10.1016/j.apenergy.2018.01.023
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_generic import generic_constraints as gen_con

GROUP_ID = "sto_"


# --------------------------------------------------------------------------- #
# Module-specific expressions
# --------------------------------------------------------------------------- #
def _p_initial_soc(model: pyo.ConcreteModel, e: str):
    """Return the maximum generation capacity of a entity for a modelled time-slice."""
    soc_ratio_y0 = cnf.DATA.get_const(e, "initial_soc_ratio")
    c_rate = cnf.DATA.get_const(e, "c_rate")
    cap_to_act = cnf.DATA.get(e, "capacity_to_activity", model.Y.first())
    ctot_0 = cnf.DATA.get(e, "actual_capacity", model.Y.first())
    return soc_ratio_y0 * c_rate * cap_to_act * ctot_0


def _e_cost_total(model: pyo.ConcreteModel):
    """Calculate the total cost of this module."""
    return sum(model.e_CostInv[e] + model.e_CostFixedOM[e] + model.e_CostVarOM[e] for e in model.Stors)


# --------------------------------------------------------------------------- #
# Module-specific constraints
# --------------------------------------------------------------------------- #
def _c_activity_setup(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Ensure generic and module-specific variables match the model setup.

    For storage, the total activity is equal to the sum of charge and discharge (w/efficiencies).
    """
    charge = sum(
        model.fin[f, ex, y, d, h] * cnf.DATA.get_fxe(e, "input_efficiency", f, y)
        for f, ex in model.StorsFiE
        if ex == e
    )
    discharge = sum(
        model.fout[f, ex, y, d, h] / cnf.DATA.get_fxe(e, "output_efficiency", f, y)
        for f, ex in model.StorsFoE
        if ex == e
    )
    return model.a[e, y, d, h] == charge + discharge


def _c_charge_limit(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Limit the storage uptake to the available capacity."""
    cap_to_act = cnf.DATA.get(e, "capacity_to_activity", y)
    charge = sum(model.fin[f, ex, y, d, h] for f, ex in model.StorsFiE if ex == e)
    return charge <= model.ctot[e, y] * cap_to_act


def _c_discharge_limit(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Limit the storage depletion to the available capacity."""
    discharge = sum(model.fout[f, ex, y, d, h] for f, ex in model.StorsFoE if ex == e)
    return discharge <= model.ctot[e, y] * cnf.DATA.get(e, "capacity_to_activity", y)


def _c_soc_limit(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Limit the state-of-charge to the available energy capacity."""
    c_rate = cnf.DATA.get(e, "c_rate", y)
    cap_to_act = cnf.DATA.get(e, "capacity_to_activity", y)
    return model.soc[e, y, d, h] <= c_rate * model.ctot[e, y] * cap_to_act


def _c_soc_flow(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Establish the relation between input-output flows and the state-of-charge."""
    inflow = sum(
        model.fin[f, ex, y, d, h] * cnf.DATA.get_fxe(e, "input_efficiency", f, y)
        for f, ex in model.StorsFiE
        if ex == e
    )
    outflow = sum(
        model.fout[f, ex, y, d, h] / cnf.DATA.get_fxe(e, "output_efficiency", f, y)
        for f, ex in model.StorsFoE
        if ex == e
    )
    if h == model.H.first():
        soc_prev = model.sto_p_IniSoC[e]
    else:
        standing_eff = cnf.DATA.get(e, "standing_efficiency", y)
        soc_prev = (standing_eff**model.HL) * model.soc[e, y, d, h - model.HL]
    return model.soc[e, y, d, h] == soc_prev + model.HL*(inflow - outflow)


def _c_soc_intra_day_cyclic(model: pyo.ConcreteModel, e: str, y: int, d: int):
    """Make the state-of-charge cyclic within a year."""
    return model.soc[e, y, d, model.H.first()] == model.soc[e, y, d, model.H.last()]


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _init_soc(model: pyo.ConcreteModel, storage_ids: list[str]):
    """Set the initial state-of-charge of a storage technology."""
    for e in storage_ids:
        for y in model.Y:
            for d in model.D:
                model.soc[e, y, d, model.H.first()].fix(model.sto_p_IniSoC[e])


def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    storages = set(cnf.ENTITIES[cnf.ENTITIES.str.startswith(GROUP_ID)])
    model.Stors = pyo.Set(initialize=storages, ordered=False)
    model.StorsFoE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in storages},
    )
    model.StorsFiE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in storages},
    )


def _parameters(model: pyo.ConcreteModel):
    model.sto_p_IniSoC = pyo.Param(model.Stors, initialize=_p_initial_soc)


def _variables(model: pyo.ConcreteModel):
    """Create any internal variables that differ from standard settings."""
    model.soc = pyo.Var(model.Stors, model.Y, model.D, model.H, domain=pyo.NonNegativeReals, initialize=0)


def _expressions(model: pyo.ConcreteModel):
    model.sto_e_CostTotal = pyo.Expression(expr=_e_cost_total(model))


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Limits
    model.sto_c_charge_limit = pyo.Constraint(model.Stors, model.Y, model.D, model.H, rule=_c_charge_limit)
    model.sto_c_discharge_limit = pyo.Constraint(model.Stors, model.Y, model.D, model.H, rule=_c_discharge_limit)
    model.sto_c_soc_limit = pyo.Constraint(model.Stors, model.Y, model.D, model.H, rule=_c_soc_limit)
    # Flow
    model.sto_c_soc_flow = pyo.Constraint(model.Stors, model.Y, model.D, model.H, rule=_c_soc_flow)
    # Temporal connections
    model.sto_c_soc_intra_day_cyclic = pyo.Constraint(model.Stors, model.Y, model.D, rule=_c_soc_intra_day_cyclic)
    # Capacity
    model.sto_c_cap_max_annual = pyo.Constraint(model.Stors, model.Y, rule=gen_con.c_cap_max_annual)
    model.sto_c_cap_transfer = pyo.Constraint(model.Stors, model.Y, rule=gen_con.c_cap_transfer)
    model.sto_c_cap_buildrate = pyo.Constraint(model.Stors, model.Y, rule=gen_con.c_cap_buildrate)
    # Activity
    model.sto_c_activity_setup = pyo.Constraint(model.Stors, model.Y, model.D, model.H, rule=_c_activity_setup)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    _init_soc(model, model.Stors)
    gen_con.init_capacity(model, model.Stors)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    return gen_con.cost_combined(model, model.Stors, model.Y)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _parameters(model)
    _variables(model)
    _expressions(model)
    _constraints(model)
    _initialise(model)
