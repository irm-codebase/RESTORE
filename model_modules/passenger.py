# --------------------------------------------------------------------------- #
# Filename: passenger.py
# Created Date: Monday, May 8th 2023, 11:59:01 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Passenger transport sector."""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic_constraints as gen_con

GROUP_ID = "conv_pass_"


def _c_travel_time_budget(model: pyo.ConcreteModel, y):
    """Limit the available time for travel each year.

    Based on Daly et al. 2014. 10.1016/j.apenergy.2014.08.051
    """
    population = cnf.DATA.get_annual("country", "actual_population", y)
    daily_time = cnf.DATA.get_annual("country", "daily_travel_time", y)
    ttb = population * daily_time * 365
    return ttb >= model.TPERIOD * 1e6 * sum(
        sum(model.fout[f, e, y, h] for h in model.H) /
        cnf.DATA.get_fxe(e, "speed", f, y)
        for f, e in model.PassTransFoE
    )


def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    techs = set(cnf.ENTITIES[cnf.ENTITIES.str.startswith(GROUP_ID)])
    model.PassTrans = pyo.Set(initialize=techs, ordered=False)
    model.PassTransFoE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FoE if e in techs},
    )
    model.PassTransFiE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in techs},
    )


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Generics
    # Input/output
    model.pass_c_flow_in = pyo.Constraint(model.PassTrans, model.Y, model.H, rule=gen_con.c_flow_in)
    model.pass_c_flow_out = pyo.Constraint(model.PassTrans, model.Y, model.H, rule=gen_con.c_flow_out)
    # Capacity
    model.pass_c_cap_max_annual = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen_con.c_cap_max_annual)
    model.pass_c_cap_transfer = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen_con.c_cap_transfer)
    model.pass_c_cap_buildrate = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen_con.c_cap_buildrate)
    # Activity
    model.pass_c_act_cf_min_year = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen_con.c_act_cf_min_year)
    model.pass_c_act_cf_max_year = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen_con.c_act_cf_max_year)
    model.pass_c_act_max_annual = pyo.Constraint(model.PassTrans, model.YOpt, rule=gen_con.c_act_max_annual)

    model.pass_c_travel_time_budget = pyo.Constraint(model.YOpt, rule=_c_travel_time_budget)


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    gen_con.init_activity(model, model.PassTrans)
    gen_con.init_capacity(model, model.PassTrans)


# --------------------------------------------------------------------------- #
# Cost
# --------------------------------------------------------------------------- #
def get_cost(model: pyo.ConcreteModel):
    """Get a cost expression for the sector."""
    return gen_con.cost_combined(model, model.PassTrans, model.Y)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _constraints(model)
    _initialise(model)
