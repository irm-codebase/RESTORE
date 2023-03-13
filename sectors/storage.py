# --------------------------------------------------------------------------- #
# Filename: storage.py
# Path: /storage.py
# Created Date: Monday, March 13th 2023, 5:03:26 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Storage sector, based on D-EXPANSE implementation.

This sector is in heavy need of an update. It should, at least, have a state of charge.
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic as gen

GROUP_ID = "sto_"


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
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
    # Output
    model.sto_c_flow_in = pyo.Constraint(model.Stors, model.Years-model.Y0, model.Hours, rule=gen.c_flow_in)
    model.sto_c_flow_out = pyo.Constraint(model.Stors, model.Years-model.Y0, model.Hours, rule=gen.c_flow_out)
    # Capacity
    model.sto_c_cap_max_annual = pyo.Constraint(model.Stors, model.Years, rule=gen.c_cap_max_annual)
    model.sto_c_cap_transfer = pyo.Constraint(model.Stors, model.Years - model.Y0, rule=gen.c_cap_transfer)
    model.sto_c_cap_retirement = pyo.Constraint(
        model.Stors, model.Years - model.Y0, rule=gen.c_cap_retirement
    )
    model.sto_c_cap_buildrate = pyo.Constraint(model.Stors, model.Years, rule=gen.c_cap_buildrate)
    # Activity
    model.sto_c_act_ramp_up = pyo.Constraint(
        model.Stors, model.Years, model.Hours - model.H0, rule=gen.c_act_ramp_up
    )
    model.sto_c_act_ramp_down = pyo.Constraint(
        model.Stors, model.Years, model.Hours - model.H0, rule=gen.c_act_ramp_down
    )
    model.sto_c_act_max_annual = pyo.Constraint(model.Stors, model.Years, rule=gen.c_act_max_annual)
    model.sto_c_act_cf_min_hour = pyo.Constraint(
        model.Stors, model.Years, model.Hours, rule=gen.c_act_cf_min_hour
    )
    model.sto_c_act_cf_max_hour = pyo.Constraint(
        model.Stors, model.Years, model.Hours, rule=gen.c_act_cf_max_hour
    )


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    gen.init_activity(model, model.Stors)
    gen.init_capacity(model, model.Stors)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _constraints(model)
    _initialise(model)
