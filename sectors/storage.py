# --------------------------------------------------------------------------- #
# Filename: storage.py
# Path: /storage.py
# Created Date: Monday, March 13th 2023, 5:03:26 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Storage sector.

To reduce model complexity, the module re-purposes standard model variables as much as possible.
For clarity:
- fin equates to the storage uptake/inflow
- fout equates to the storage dispatch/discharge/outflow
- a equates to the storage state-of-charge

# NOTE: for now, the module does not have constraints for SoC ranges (i.e., batteries can reach limits)
# NOTE: constraints assume capacity is ALWAYS enabled (deactivation does not make sense for this module)

The constraints are based on PyPSA's storage constraints, see:
https://pypsa.readthedocs.io/en/latest/optimal_power_flow.html#storage-unit-constraints
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic as gen

GROUP_ID = "sto_"


# --------------------------------------------------------------------------- #
# Sector-specific constraints
# --------------------------------------------------------------------------- #
def _c_outflow_limit(model: pyo.ConcreteModel, storage_id: str, y: int, h: int):
    """Limit the storage depletion to the available capacity."""
    cap_to_act = cnf.DATA.get(storage_id, "capacity_to_activity", y)
    outflow = sum(model.fout[f, e, y, h] for f, e in model.StorsFoE if e == storage_id)
    return outflow / model.TS <= model.ctot[storage_id, y] * cap_to_act


def _c_inflow_limit(model: pyo.ConcreteModel, storage_id: str, y: int, h: int):
    """Limit the storage uptake to the available capacity."""
    cap_to_act = cnf.DATA.get(storage_id, "capacity_to_activity", y)
    inflow = sum(model.fin[f, e, y, h] for f, e in model.StorsFiE if e == storage_id)
    return inflow / model.TS <= model.ctot[storage_id, y] * cap_to_act


def _c_soc_limit(model: pyo.ConcreteModel, storage_id: str, y: int, h: int):
    """Limit the state-of-charge to the available energy capacity."""
    c_rate = cnf.DATA.get(storage_id, "c_rate", y)
    cap_to_act = cnf.DATA.get(storage_id, "capacity_to_activity", y)
    return model.a[storage_id, y, h] <= c_rate * model.ctot[storage_id, y] * cap_to_act


def _c_soc_flow(model: pyo.ConcreteModel, storage_id: str, y: int, h: int):
    """Establish the relation between input-output flows and the state-of-charge."""
    inflow = sum(
        model.fin[f, e, y, h] * cnf.DATA.get_fxe(storage_id, "input_efficiency", f, y)
        for f, e in model.StorsFiE
        if e == storage_id
    )
    outflow = sum(
        model.fout[f, e, y, h] / cnf.DATA.get_fxe(storage_id, "output_efficiency", f, y)
        for f, e in model.StorsFoE
        if e == storage_id
    )
    if h == model.Hours.first():
        soc_prev = model.TS * (model.a[storage_id, model.Y0.first(), model.H0.first()] + inflow - outflow)
    else:
        standing_eff = cnf.DATA.get(storage_id, "standing_efficiency", y)
        soc_prev = model.TS * (standing_eff * model.a[storage_id, y, h - 1] + inflow - outflow)
    return model.a[storage_id, y, h] == soc_prev


def _c_soc_intra_year_cyclic(model: pyo.ConcreteModel, storage_id: str, y: int):
    """Make the state-of-charge cyclic within a year."""
    if cnf.DATA.check_cnf(storage_id, "enable_cyclic") is None:
        return pyo.Constraint.Skip
    return model.a[storage_id, y, model.Hours.first()] == model.a[storage_id, y, model.Hours.last()]


def _c_soc_inter_year(model: pyo.ConcreteModel, storage_id: str, y: int):
    """Connect the final SoC between years."""
    return model.a[storage_id, y - 1, model.Hours.last()] == model.a[storage_id, y, model.Hours.first()]


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _init_soc(model: pyo.ConcreteModel, storage_ids: list[str]):
    """Set the initial state-of-charge of a storage technology."""
    y_0 = model.Y0.first()
    for e in storage_ids:
        enable_year = cnf.DATA.check_cnf(e, "enable_year")
        if enable_year <= y_0:
            soc_y0 = cnf.DATA.get_const(e, "initial_soc_ratio")
            cap_y0 = cnf.DATA.get_annual(e, "actual_capacity", y_0)
            c_rate = cnf.DATA.get_const(e, "c_rate")
            cap_to_act = cnf.DATA.get(e, "capacity_to_activity", y_0)
            model.a[e, y_0, model.Hours.first()].fix(soc_y0 * cap_y0 * c_rate * cap_to_act)


def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    storages = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith(GROUP_ID)])
    model.Stors = pyo.Set(initialize=storages, ordered=False)
    model.StorsFoE = pyo.Set(
        within=model.Flows * model.Elems,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in storages},
    )
    model.StorsFiE = pyo.Set(
        within=model.Flows * model.Elems,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in storages},
    )


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Limits
    model.sto_c_outflow_limit = pyo.Constraint(model.Stors, model.Years, model.Hours, rule=_c_outflow_limit)
    model.sto_c_inflow_limit = pyo.Constraint(model.Stors, model.Years, model.Hours, rule=_c_inflow_limit)
    model.sto_c_soc_limit = pyo.Constraint(model.Stors, model.Years, model.Hours, rule=_c_soc_limit)
    # Flow
    model.sto_c_soc_flow = pyo.Constraint(model.Stors, model.Years, model.Hours, rule=_c_soc_flow)
    # Temporal connections
    model.sto_c_soc_intra_year_cyclic = pyo.Constraint(
        model.Stors, model.Years, rule=_c_soc_intra_year_cyclic
    )
    model.sto_c_soc_inter_year = pyo.Constraint(model.Stors, model.YOpt, rule=_c_soc_inter_year)
    # Capacity
    model.sto_c_cap_max_annual = pyo.Constraint(model.Stors, model.YOpt, rule=gen.c_cap_max_annual)
    model.sto_c_cap_transfer = pyo.Constraint(model.Stors, model.YOpt, rule=gen.c_cap_transfer)
    model.sto_c_cap_retirement = pyo.Constraint(model.Stors, model.YOpt, rule=gen.c_cap_retirement)
    model.sto_c_cap_buildrate = pyo.Constraint(model.Stors, model.YOpt, rule=gen.c_cap_buildrate)
    # Activity
    # model.sto_c_act_max_annual = pyo.Constraint(model.Stors, model.YOpt, rule=gen.c_act_max_annual)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    _init_soc(model, model.Stors)
    gen.init_capacity(model, model.Stors)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    return gen.cost_combined(model, model.Stors, model.Years)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _constraints(model)
    _initialise(model)
