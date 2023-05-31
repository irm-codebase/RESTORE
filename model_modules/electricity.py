# --------------------------------------------------------------------------- #
# Filename: electricity.py
# Created Date: Tuesday, May 16th 2023, 5:39:39 pm
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Electricity sector, based in D-EXPANSE functionality."""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import data_handler
from model_generic import generic_constraints as gen_con

GROUP_IDS = ["conv_chp_", "conv_elec_"]
OUTFLOW_ID = "elecsupply"

VRE_NAMES = ["onshorewind", "pv", "offshorewind"]
VRE_DICT = data_handler.get_lf_vre(cnf.ISO2)


# --------------------------------------------------------------------------- #
# Module-specific expressions
# --------------------------------------------------------------------------- #
def _e_cost_total(model: pyo.ConcreteModel):
    """Calculate the total cost of Extraction entities."""
    return sum(model.e_CostInv[e] + model.e_CostFixedOM[e] + model.e_CostVarOM[e] for e in model.Elecs)


# --------------------------------------------------------------------------- #
# Module-specific constraints
# --------------------------------------------------------------------------- #
def _c_act_cf_max_hour(model: pyo.ConcreteModel, e: str, y: int, d: int, h: int):
    """Set the maximum hourly utilisation of an entity's capacity.

    Accounts for VRE load factors.
    """
    if not cnf.DATA.check_cnf(e, "enable_capacity"):
        return pyo.Constraint.Skip
    if e in model.ElecsVRE:
        lf_max = VRE_DICT[e][y, h % 24]
    else:
        lf_max = cnf.DATA.get(e, "lf_max", y)
    return model.a[e, y, d, h] <= lf_max * model.ctot[e, y] * model.e_HourlyC2A[e, y]


# TODO: needs to be more robust... will break if several countries are present.
def _c_cap_peak(model: pyo.ConcreteModel, y: int):
    """Peak capacity requirement must be met excluding import (full autarky)."""
    f = OUTFLOW_ID
    cap_margin = cnf.DATA.get(f, "peak_capacity_margin", y)
    if cap_margin is None:
        raise ValueError("Peak capacity margin must be configured for", f)
    peak_power = cnf.DATA.get_annual(f, "peak_capacity_demand", y)
    pk_cap_sys = sum(
            model.ctot[e, y] * cnf.DATA.get_fxe(e, "output_efficiency", fx, y) * cnf.DATA.get(e, "peak_ratio", y)
            for fx, e in model.FoE
            if fx == f and e in (model.Caps - model.Trades)
    )
    return pk_cap_sys >= (1 + cap_margin) * peak_power


def _c_cap_base(model, y):
    """Meet base capacity requirement, including imports."""
    f = OUTFLOW_ID
    base_power = cnf.DATA.get_annual(f, "base_capacity_demand", y)
    base_cap_sys = sum(
        model.ctot[e, y] * cnf.DATA.get_fxe(e, "output_efficiency", fx, y) * cnf.DATA.get(e, "lf_min", y)
        for fx, e in model.FoE
        if fx == f and e in (model.Caps - model.Trades)
    )
    export_capacity = sum(
        model.ctot[e, y] * cnf.DATA.get_fxe(e, "input_efficiency", fx, y)
        for fx, e in model.FoE
        if fx == f and e in (model.Trades & model.Caps)
    )
    if isinstance(base_cap_sys, int):
        print(f"Warning: Skipped base capacity requirement of {base_cap_sys} for {y}. Check LF data.")
        return pyo.Constraint.Skip
    constraint = base_power >= base_cap_sys - export_capacity
    return constraint  # System must be able to go lower than the lowest expected demand


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    elec_entities = set()  # type: set[str]
    for group in GROUP_IDS:
        elec_entities = elec_entities | set(cnf.ENTITIES[cnf.ENTITIES.str.startswith(group)])
    model.Elecs = pyo.Set(initialize=elec_entities, ordered=False)

    vre_entities = set(c for c in elec_entities for vre in VRE_NAMES if vre in c)
    model.ElecsVRE = pyo.Set(initialize=vre_entities, ordered=False)

    model.ElecsFoE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in elec_entities},
    )
    model.ElecsFiE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in elec_entities},
    )


def _expressions(model: pyo.ConcreteModel):
    model.elec_e_CostTotal = pyo.Expression(expr=_e_cost_total(model))


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints.

    Includes CHP, for now.
    """
    # Generics
    # Input/output
    model.elec_c_flow_in = pyo.Constraint(model.Elecs, model.Y, model.D, model.H, rule=gen_con.c_flow_in)
    model.elec_c_flow_out = pyo.Constraint(model.Elecs, model.Y, model.D, model.H, rule=gen_con.c_flow_out)
    # Capacity
    model.elec_c_cap_max_annual = pyo.Constraint(model.Elecs, model.Y, rule=gen_con.c_cap_max_annual)
    model.elec_c_cap_transfer = pyo.Constraint(model.Elecs, model.Y, rule=gen_con.c_cap_transfer)
    model.elec_c_cap_buildrate = pyo.Constraint(model.Elecs, model.Y, rule=gen_con.c_cap_buildrate)
    # Activity
    model.elec_c_act_ramp_up = pyo.Constraint(
        model.Elecs, model.Y, model.D, model.H - model.H0, rule=gen_con.c_act_ramp_up
    )
    model.elec_c_act_ramp_down = pyo.Constraint(
        model.Elecs, model.Y, model.D, model.H - model.H0, rule=gen_con.c_act_ramp_down
    )
    model.elec_c_act_max_annual = pyo.Constraint(model.Elecs, model.Y, rule=gen_con.c_act_max_annual)
    model.elec_c_act_cf_min_hour = pyo.Constraint(
        model.Elecs, model.Y, model.D, model.H, rule=gen_con.c_act_cf_min_hour
    )

    # Sector specific
    model.elec_c_act_cf_max_hour = pyo.Constraint(model.Elecs, model.Y, model.D, model.H, rule=_c_act_cf_max_hour)
    # Peak and base-load capacity requirements
    model.elec_c_cap_peak = pyo.Constraint(model.Y, rule=_c_cap_peak)
    model.elec_c_cap_base = pyo.Constraint(model.Y, rule=_c_cap_base)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    gen_con.init_capacity(model, model.Elecs)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    return gen_con.cost_combined(model, model.Elecs, model.Y)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _expressions(model)
    _constraints(model)
    _initialise(model)
