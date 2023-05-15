# --------------------------------------------------------------------------- #
# Filename: enertransp.py
# Path: /enertransp.py
# Created Date: Monday, March 13th 2023, 5:27:09 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Energy transport sector.

For now, only electricity transmission/distribution.
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic_constraints as gen_con

GROUP_ID = "conv_transmission"


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    storages = set(cnf.ENTITIES[cnf.ENTITIES.str.startswith(GROUP_ID)])
    model.ETrans = pyo.Set(initialize=storages, ordered=False)
    model.ETransFoE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in storages},
    )
    model.ETransFiE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in storages},
    )


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Input/output
    model.etrans_c_flow_in = pyo.Constraint(model.ETrans, model.Y, model.H, rule=gen_con.c_flow_in)
    model.etrans_c_flow_out = pyo.Constraint(model.ETrans, model.Y, model.H, rule=gen_con.c_flow_out)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    gen_con.init_activity(model, model.ETrans)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    return gen_con.cost_variable_om(model, model.ETrans, model.Y)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _constraints(model)
    _initialise(model)
