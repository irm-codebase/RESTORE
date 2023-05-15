# --------------------------------------------------------------------------- #
# Filename: electricity.py
# Path: /electricity.py
# Created Date: Friday, March 10th 2023, 5:14:21 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Electricity sector, based in D-EXPANSE functionality."""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import data_handler
from model_utils import generic_constraints as gen_con

GROUP_IDS = ["conv_chp_", "conv_elec_"]
OUTFLOW_ID = "elecsupply"

VRE_NAMES = ["onshorewind", "pv", "offshorewind"]
VRE_DICT = data_handler.get_lf_vre(cnf.ISO2)


# --------------------------------------------------------------------------- #
# Sector-specific constraints
# --------------------------------------------------------------------------- #
def _c_act_cf_max_hour(model, entity_id, y, h):
    """Set the maximum hourly utilisation of an entity's capacity.

    Accounts for VRE load factors.
    """
    enable_year = cnf.DATA.check_cnf(entity_id, "enable_year")
    if not cnf.DATA.check_cnf(entity_id, "enable_capacity") or y <= enable_year:
        return pyo.Constraint.Skip
    if entity_id in model.ElecsVRE:
        lf_max = VRE_DICT[entity_id][y, h % 24]
    else:
        lf_max = cnf.DATA.get(entity_id, "lf_max", y)
    cap_to_act = cnf.DATA.get(entity_id, "capacity_to_activity", y) / model.YH
    return model.a[entity_id, y, h] <= lf_max * model.ctot[entity_id, y] * cap_to_act


def _c_cap_peak(model, y):
    """Fulfil capacity requirement, excluding import capacity (full autarky)."""
    flow_id = OUTFLOW_ID
    cap_margin = cnf.DATA.get(flow_id, "peak_capacity_margin", y)
    if cap_margin is None:
        raise ValueError("Peak capacity margin must be configured for", flow_id)
    peak_power = cnf.DATA.get_annual(flow_id, "peak_capacity_demand", y)
    pk_cap_sys = sum(
        [
            model.ctot[e, y]
            * cnf.DATA.get_fxe(e, "output_efficiency", f, y)
            * cnf.DATA.get(e, "peak_ratio", y)
            for f, e in model.FoE
            if f == flow_id and e in (model.Caps - model.Trades)
        ]
    )
    return pk_cap_sys >= (1 + cap_margin) * peak_power


def _c_cap_base(model, y):
    """Meet base capacity requirement, with the help of imports."""
    flow_id = OUTFLOW_ID
    base_power = cnf.DATA.get_annual(flow_id, "base_capacity_demand", y)
    base_cap_sys = sum(
        [
            model.ctot[e, y] * cnf.DATA.get_fxe(e, "output_efficiency", f, y) * cnf.DATA.get(e, "lf_min", y)
            for f, e in model.FoE
            if f == flow_id and e in (model.Caps - model.Trades)
        ]
    )
    imports = sum(
        [
            model.ctot[e, y] * cnf.DATA.get_fxe(e, "output_efficiency", f, y)
            for f, e in model.FoE
            if f == flow_id and e in (model.Trades & model.Caps)
        ]
    )
    if isinstance(base_cap_sys, int):
        print(f"Warning: Skipped base capacity requirement of {base_cap_sys} for {y}. Check LF data.")
        return pyo.Constraint.Skip
    constraint = base_power >= base_cap_sys - imports
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


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints.

    Includes CHP, for now.
    """
    # Generics
    # Input/output
    model.elec_c_flow_in = pyo.Constraint(model.Elecs, model.Y, model.H, rule=gen_con.c_flow_in)
    model.elec_c_flow_out = pyo.Constraint(model.Elecs, model.Y, model.H, rule=gen_con.c_flow_out)
    # Capacity
    model.elec_c_cap_max_annual = pyo.Constraint(model.Elecs, model.YOpt, rule=gen_con.c_cap_max_annual)
    model.elec_c_cap_transfer = pyo.Constraint(model.Elecs, model.YOpt, rule=gen_con.c_cap_transfer)
    model.elec_c_cap_retirement = pyo.Constraint(model.Elecs, model.YOpt, rule=gen_con.c_cap_retirement)
    model.elec_c_cap_buildrate = pyo.Constraint(model.Elecs, model.YOpt, rule=gen_con.c_cap_buildrate)
    # Activity
    model.elec_c_act_ramp_up = pyo.Constraint(
        model.Elecs, model.YOpt, model.H - model.H0, rule=gen_con.c_act_ramp_up
    )
    model.elec_c_act_ramp_down = pyo.Constraint(
        model.Elecs, model.YOpt, model.H - model.H0, rule=gen_con.c_act_ramp_down
    )
    model.elec_c_act_max_annual = pyo.Constraint(model.Elecs, model.YOpt, rule=gen_con.c_act_max_annual)
    model.elec_c_act_cf_min_hour = pyo.Constraint(
        model.Elecs, model.YOpt, model.H, rule=gen_con.c_act_cf_min_hour
    )

    # Sector specific
    # Max LF per hour
    model.elec_c_act_cf_max_hour = pyo.Constraint(
        model.Elecs, model.YOpt, model.H, rule=_c_act_cf_max_hour
    )
    # Peak and base-load capacity requirements
    model.elec_c_cap_peak = pyo.Constraint(model.YOpt, rule=_c_cap_peak)
    model.elec_c_cap_base = pyo.Constraint(model.YOpt, rule=_c_cap_base)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    gen_con.init_activity(model, model.Elecs)
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
    _constraints(model)
    _initialise(model)
