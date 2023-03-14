# --------------------------------------------------------------------------- #
# Filename: extraction.py
# Path: /extraction.py
# Created Date: Monday, March 13th 2023, 3:48:10 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Extraction sector."""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic as gen

GROUP_ID = "ext_"


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    extractions = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith(GROUP_ID)])
    model.Extrs = pyo.Set(initialize=extractions, ordered=False)
    model.ExtrsFoE = pyo.Set(
        within=model.Flows * model.Elems,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in extractions},
    )


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Output
    model.ext_c_flow_out = pyo.Constraint(model.Extrs, model.YOpt, model.Hours, rule=gen.c_flow_out)
    # Capacity
    model.ext_c_cap_max_annual = pyo.Constraint(model.Extrs, model.Years, rule=gen.c_cap_max_annual)
    model.ext_c_cap_transfer = pyo.Constraint(model.Extrs, model.YOpt, rule=gen.c_cap_transfer)
    model.ext_c_cap_retirement = pyo.Constraint(model.Extrs, model.YOpt, rule=gen.c_cap_retirement)
    model.ext_c_cap_buildrate = pyo.Constraint(model.Extrs, model.Years, rule=gen.c_cap_buildrate)
    # Activity
    model.ext_c_act_ramp_up = pyo.Constraint(
        model.Extrs, model.Years, model.Hours - model.H0, rule=gen.c_act_ramp_up
    )
    model.ext_c_act_ramp_down = pyo.Constraint(
        model.Extrs, model.Years, model.Hours - model.H0, rule=gen.c_act_ramp_down
    )
    model.ext_c_act_max_annual = pyo.Constraint(model.Extrs, model.Years, rule=gen.c_act_max_annual)
    model.ext_c_act_cf_min_hour = pyo.Constraint(
        model.Extrs, model.Years, model.Hours, rule=gen.c_act_cf_min_hour
    )
    model.ext_c_act_cf_max_hour = pyo.Constraint(
        model.Extrs, model.Years, model.Hours, rule=gen.c_act_cf_max_hour
    )


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    # gen.init_activity(model, model.Extrs)
    gen.init_capacity(model, model.Extrs)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    return gen.cost_combined(model, model.Extrs, model.Years)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _constraints(model)
    _initialise(model)
