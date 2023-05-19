# --------------------------------------------------------------------------- #
# Filename: extraction.py
# Created Date: Monday, May 8th 2023, 11:58:58 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Extraction sector."""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic_constraints as gen_con

GROUP_ID = "ext_"


# --------------------------------------------------------------------------- #
# Sector-specific expressions
# --------------------------------------------------------------------------- #
def _e_cost_total(model: pyo.ConcreteModel):
    """Calculate the total cost of Extraction entities."""
    return sum(model.e_CostInv[e] + model.e_CostFixedOM[e] + model.e_CostVarOM[e] for e in model.Extrs)


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    extractions = set(cnf.ENTITIES[cnf.ENTITIES.str.startswith(GROUP_ID)])
    model.Extrs = pyo.Set(initialize=extractions, ordered=False)
    model.ExtrsFoE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in extractions},
    )


def _expressions(model: pyo.ConcreteModel):
    model.ext_e_CostTotal = pyo.Expression(expr=_e_cost_total(model))


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Output
    model.ext_c_flow_out = pyo.Constraint(model.Extrs, model.Y, model.D, model.H, rule=gen_con.c_flow_out)
    # Capacity
    model.ext_c_cap_max_annual = pyo.Constraint(model.Extrs, model.Y, rule=gen_con.c_cap_max_annual)
    model.ext_c_cap_transfer = pyo.Constraint(model.Extrs, model.Y, rule=gen_con.c_cap_transfer)
    model.ext_c_cap_buildrate = pyo.Constraint(model.Extrs, model.Y, rule=gen_con.c_cap_buildrate)
    # Activity
    model.ext_c_act_ramp_up = pyo.Constraint(
        model.Extrs, model.Y, model.D, model.H - model.H0, rule=gen_con.c_act_ramp_up
    )
    model.ext_c_act_ramp_down = pyo.Constraint(
        model.Extrs, model.Y, model.D, model.H - model.H0, rule=gen_con.c_act_ramp_down
    )
    model.ext_c_act_max_annual = pyo.Constraint(model.Extrs, model.Y, rule=gen_con.c_act_max_annual)
    model.ext_c_act_cf_min_hour = pyo.Constraint(
        model.Extrs, model.Y, model.D, model.H, rule=gen_con.c_act_cf_min_hour
    )
    model.ext_c_act_cf_max_hour = pyo.Constraint(
        model.Extrs, model.Y, model.D, model.H, rule=gen_con.c_act_cf_max_hour
    )


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    # gen.init_activity(model, model.Extrs)
    gen_con.init_capacity(model, model.Extrs)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _expressions(model)
    _constraints(model)
    _initialise(model)
