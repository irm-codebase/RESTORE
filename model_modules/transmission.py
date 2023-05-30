# --------------------------------------------------------------------------- #
# Filename: transmission.py
# Created Date: Monday, May 8th 2023, 11:59:08 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Energy transport sector.

For now, only electricity transmission/distribution.
# TODO: The transmission Kirchhoff voltage constraint in EXPANSE could be put here to enable spatial modelling.
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_generic import generic_constraints as gen_con

GROUP_ID = "conv_transmission"


# --------------------------------------------------------------------------- #
# Module-specific expressions
# --------------------------------------------------------------------------- #
def _e_cost_total(model: pyo.ConcreteModel):
    """Calculate the total cost of Extraction entities."""
    return sum(model.e_CostVarOM[e] for e in model.ETrans)


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


def _expressions(model: pyo.ConcreteModel):
    model.etrans_e_CostTotal = pyo.Expression(expr=_e_cost_total(model))


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Input/output
    model.etrans_c_flow_in = pyo.Constraint(model.ETrans, model.Y, model.D, model.H, rule=gen_con.c_flow_in)
    model.etrans_c_flow_out = pyo.Constraint(model.ETrans, model.Y, model.D, model.H, rule=gen_con.c_flow_out)


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
    _expressions(model)
    _constraints(model)
    # _initialise(model)
