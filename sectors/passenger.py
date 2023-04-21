# --------------------------------------------------------------------------- #
# Filename: passenger.py
# Path: /passenger.py
# Created Date: Tuesday, March 14th 2023, 11:15:35 am
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Passenger transport sector."""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic as gen

GROUP_ID = "conv_pass_"


def _c_travel_time_budget(model: pyo.ConcreteModel, y):
    """Limit the available time for travel each year.

    Based on Daly et al. 2014. 10.1016/j.apenergy.2014.08.051
    """
    population = cnf.DATA.get_annual("country", "actual_population", y)
    daily_time = cnf.DATA.get_annual("country", "daily_travel_time", y)
    ttb = population * daily_time * 365
    return ttb >= model.TPERIOD * 1e6 * sum(
        sum(model.fout[f, e, y, h] for h in model.Hours) /
        cnf.DATA.get_fxe(e, "speed", f, y)
        for f, e in model.PassTransFoE
    )


def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    techs = set(cnf.ELEMENTS[cnf.ELEMENTS.str.startswith(GROUP_ID)])
    model.PassTrans = pyo.Set(initialize=techs, ordered=False)
    model.PassTransFoE = pyo.Set(
        within=model.Flows * model.Elems,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in techs},
    )
    model.PassTransFiE = pyo.Set(
        within=model.Flows * model.Elems,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in techs},
    )


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Generics
    # Input/output
    model.pass_c_flow_in = pyo.Constraint(model.PassTrans, model.Years, model.Hours, rule=gen.c_flow_in)
    model.pass_c_flow_out = pyo.Constraint(model.PassTrans, model.Years, model.Hours, rule=gen.c_flow_out)
    # Capacity
    model.pass_c_cap_max_annual = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen.c_cap_max_annual)
    model.pass_c_cap_transfer = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen.c_cap_transfer)
    model.pass_c_cap_retirement = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen.c_cap_retirement)
    model.pass_c_cap_buildrate = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen.c_cap_buildrate)
    # Activity
    model.pass_c_act_cf_min_year = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen.c_act_cf_min_year)
    model.pass_c_act_cf_max_year = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen.c_act_cf_max_year)
    model.pass_c_act_max_annual = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen.c_act_max_annual)

    model.pass_c_travel_time_budget = pyo.Constraint(model.YOpt, rule=_c_travel_time_budget)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    gen.init_activity(model, model.PassTrans)
    gen.init_capacity(model, model.PassTrans)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    return gen.cost_combined(model, model.PassTrans, model.Years)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _constraints(model)
    _initialise(model)
