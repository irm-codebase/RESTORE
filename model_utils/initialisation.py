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
import configuration as cnf
import data_handler


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
    model.Hours = pyo.Set(initialize=cnf.HOURS, ordered=True)
    model.H0 = pyo.Set(initialize=[cnf.HOURS[0]], ordered=True)

    # Structural (1xN)
    elements = set(cnf.ELEMENTS)
    flows = set(cnf.FLOWS)
    model.Elems = pyo.Set(initialize=elements, ordered=False)
    model.Flows = pyo.Set(initialize=flows, ordered=False)

    # Element sub-types (1xN)
    conversions = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith("conv_")])
    extractions = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith("ext_")])
    trades = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith("trd_")])
    storages = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith("sto_")])
    demands = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith("dem_")])
    model.Convs = pyo.Set(initialize=conversions, ordered=False)
    model.Extrs = pyo.Set(initialize=extractions, ordered=False)
    model.Trades = pyo.Set(initialize=trades, ordered=False)
    model.Stors = pyo.Set(initialize=storages, ordered=False)
    model.Dems = pyo.Set(initialize=demands, ordered=False)

    # Element groupings (1xN)
    processes = elements - demands
    capacity = cnf.DATA.build_cnf_set(processes, "enable_capacity")
    model.Pros = pyo.Set(initialize=processes, ordered=False)
    model.ProsCap = pyo.Set(initialize=capacity, ordered=False)

    # Connections (FxE), using cartesian subsets
    # See https://github.com/brentertainer/pyomo-tutorials/blob/master/intermediate/05-indexed-sets.ipynb
    f_in = data_handler.get_flow_element_dict(cnf.DATA.fxe["FiE"])  # Must not contain Extractions
    f_out = data_handler.get_flow_element_dict(cnf.DATA.fxe["FoE"])  # Must not contain Demands
    f_inout_e = data_handler.merge_dicts(f_out, f_in)
    fxe = model.Flows * model.Elems
    model.FiE = pyo.Set(within=fxe, ordered=False, initialize={(f, p) for f in flows for p in f_in[f]})
    model.FoE = pyo.Set(within=fxe, ordered=False, initialize={(f, p) for f in flows for p in f_out[f]})
    model.FxE = pyo.Set(within=fxe, ordered=False, initialize={(f, p) for f in flows for p in f_inout_e[f]})

    return model


def _init_variables(model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    # Capacity TODO: find a way of eliminating unnecessary capacity variables
    model.ctot = pyo.Var(model.ProsCap, model.Years, domain=pyo.NonNegativeReals, initialize=0)
    model.cnew = pyo.Var(model.ProsCap, model.Years, domain=pyo.NonNegativeReals, initialize=0)
    model.cret = pyo.Var(model.ProsCap, model.Years, domain=pyo.NonNegativeReals, initialize=0)

    # Process activity
    act = model.Elems - model.Trades
    model.a = pyo.Var(act, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)
    model.aimp = pyo.Var(model.TradesImp, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)
    model.aexp = pyo.Var(model.TradesExp, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)

    # Flows
    model.fin = pyo.Var(model.FiE, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)
    model.fout = pyo.Var(model.FoE, model.Years, model.Hours, domain=pyo.NonNegativeReals, initialize=0)

    return model


def _init_parameters(model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    model.NDAYS = pyo.Param(initialize=cnf.NDAYS, doc="Number of representative days")
    model.TPERIOD = pyo.Param(initialize=365/cnf.NDAYS, doc="Adjust from representative days to year")
    model.DR = pyo.Param(model.Years, initialize=_discount_rates, doc="Discount Rates")

    return model


def init_model() -> pyo.ConcreteModel:
    """Create model structure."""
    # Initialise model
    model = pyo.ConcreteModel()
    model = _init_sets(model)
    model = _init_variables(model)
    model = _init_parameters(model)

    model.c_io_balance = pyo.Constraint(model.Flows, model.Years-model.Y0, model.Hours, rule=_c_io_balance)

    return model
