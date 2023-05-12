# --------------------------------------------------------------------------- #
# Filename: initialisation.py
# Path: /initialisation.py
# Created Date: Friday, March 10th 2023, 2:53:02 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Contains all necessary functionality needed to initialise the model.

Must only contain functionality applicable to the entire model.

Rules:
- No sector-specific Sets.
- No global constants. Those go in configuration.py.
- This module shall not be used by sector files.
- Only include constraints that are essential to the model architecture.
"""
import numpy as np
import pyomo.environ as pyo
from model_utils import configuration as cnf
from model_utils import data_handler


def _c_io_balance(model: pyo.ConcreteModel, flow_id: str, y: int, h: int):
    """Balance inputs and outputs at every flow bus."""
    outflows_prev = sum(model.fout[f, e, y, h] for (f, e) in model.FoE if f == flow_id)
    inflows_next = sum(model.fin[f, e, y, h] for (f, e) in model.FiE if f == flow_id)
    return outflows_prev == inflows_next


def _discount_rates(mod, year):
    discount = cnf.DATA.get_const("country", "discount_factor")
    return 1 / np.power(1 + discount, (year - mod.Years.first()))


def _init_sets(model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    # Temporal (1xN)
    model.Years = pyo.Set(initialize=cnf.YEARS, ordered=True)
    model.Y0 = pyo.Set(initialize=[cnf.YEARS[0]], ordered=True)
    model.YOpt = pyo.Set(initialize=model.Years - model.Y0, ordered=True)
    model.Hours = pyo.Set(initialize=cnf.HOURS, ordered=True)
    model.H0 = pyo.Set(initialize=[cnf.HOURS[0]], ordered=True)

    # Structural (1xN)
    entities = set(cnf.ENTITIES)
    flows = set(cnf.FLOWS)
    model.Ents = pyo.Set(initialize=entities, ordered=False)
    model.Flows = pyo.Set(initialize=flows, ordered=False)

    # Entity groupings (1xN)
    demands = set(cnf.ENTITIES[cnf.ENTITIES.str.startswith("dem_")])
    processes = entities - demands
    capacity = cnf.DATA.build_cnf_set(processes, "enable_capacity")
    model.Pros = pyo.Set(initialize=processes, ordered=False)
    model.Caps = pyo.Set(initialize=capacity, ordered=False)

    # Connections (FxE), using cartesian subsets
    # See https://github.com/brentertainer/pyomo-tutorials/blob/master/intermediate/05-indexed-sets.ipynb
    f_in = data_handler.get_flow_entity_dict(cnf.DATA.fxe["FiE"])  # Must not contain Extractions
    f_out = data_handler.get_flow_entity_dict(cnf.DATA.fxe["FoE"])  # Must not contain Demands
    f_inout_e = data_handler.merge_dicts(f_out, f_in)
    fxe = model.Flows * model.Ents
    model.FiE = pyo.Set(within=fxe, ordered=False, initialize={(f, p) for f in flows for p in f_in[f]})
    model.FoE = pyo.Set(within=fxe, ordered=False, initialize={(f, p) for f in flows for p in f_out[f]})
    model.FxE = pyo.Set(within=fxe, ordered=False, initialize={(f, p) for f in flows for p in f_inout_e[f]})

    return model


def _init_variables(model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    model.ctot = pyo.Var(model.Caps, model.Years, domain=pyo.NonNegativeReals, initialize=0)
    model.cnew = pyo.Var(model.Caps, model.Years, domain=pyo.NonNegativeReals, initialize=0)
    model.cret = pyo.Var(model.Caps, model.Years, domain=pyo.NonNegativeReals, initialize=0)

    # Process activity
    model.a = pyo.Var(model.Ents, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)

    # Flows
    model.fin = pyo.Var(model.FiE, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)
    model.fout = pyo.Var(model.FoE, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)

    return model


def _init_parameters(model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    model.NDAYS = pyo.Param(initialize=cnf.NDAYS, doc="Number of representative days")
    model.TPERIOD = pyo.Param(initialize=365/cnf.NDAYS, doc="Adjust from representative days to year")
    model.TS = pyo.Param(initialize=cnf.TIMESLICE, doc="Length of a time-slice in the model")
    model.YH = pyo.Param(initialize=365*24, doc="Number of hours in the year")

    model.DR = pyo.Param(model.Years, initialize=_discount_rates, doc="Discount Rates")

    return model


def init_model() -> pyo.ConcreteModel:
    """Create model structure."""
    # Initialise model
    model = pyo.ConcreteModel()
    model = _init_sets(model)
    model = _init_variables(model)
    model = _init_parameters(model)

    model.c_io_balance = pyo.Constraint(model.Flows, model.YOpt, model.Hours, rule=_c_io_balance)

    return model
