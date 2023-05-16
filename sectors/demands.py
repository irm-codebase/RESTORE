# --------------------------------------------------------------------------- #
# Filename: demands.py
# Path: /demands.py
# Created Date: Tuesday, March 14th 2023, 11:39:59 am
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Demands sector.

Although 'sector' is a bit of a misnomer, this module is meant to keep the demand-building
functions separate from the rest of the code.
"""
import pyomo.environ as pyo

from model_utils import configuration as cnf
from model_utils import generic_constraints as gen_con
from gen_utils import k_clustering

GROUP_ID = "dem_"


# --------------------------------------------------------------------------- #
# Sector-specific expressions
# --------------------------------------------------------------------------- #
def _e_cost_total(model: pyo.ConcreteModel):
    """Calculate the total cost of Extraction entities."""
    return sum(model.e_CostVarOM[e] for e in model.Dems)


# --------------------------------------------------------------------------- #
# Sector-specific constraints
# --------------------------------------------------------------------------- #
def _init_dem_elec(model: pyo.ConcreteModel):
    """Electricity demand is taken using K-Means, for now."""
    # Set electricity demand
    elec_demand_y = [cnf.DATA.get_annual("dem_elec", "actual_demand", y) for y in model.Y]
    ratio, elec_demand_y_h = k_clustering.get_demand_shape(cnf.ISO3, model.Y, cnf.NDAYS, elec_demand_y)
    # Convert back into TWh and remove the array shape
    # TODO: move the magic value to the demand file to enable conversion regardless of the setting?
    elec_demand_y_h = {key: value / 1000 for key, value in elec_demand_y_h.items()}

    for y in model.Y:
        for d in model.D:
            model.DL[y, d].value = ratio[y][d]*365
            for h in model.H:
                model.a["dem_elec", y, d, h].fix(elec_demand_y_h[y][d][h])


def _init_dem_passenger(model: pyo.ConcreteModel):
    """Passenger demand uses the demand shape from the STEM model, for now."""
    # Set passenger travel demand
    # TODO: temporary until a standard file for load shapes is created
    pass_demand_shape = [
        0,
        0,
        0,
        0.001672241,
        0.003344482,
        0.013377926,
        0.050167224,
        0.066889632,
        0.050167224,
        0.046822742,
        0.046822742,
        0.063545151,
        0.060200669,
        0.070234114,
        0.056856187,
        0.060200669,
        0.08361204,
        0.093645485,
        0.075250836,
        0.058528428,
        0.033444816,
        0.026755853,
        0.025083612,
        0.013377926,
    ]

    for y in model.Y:
        for h in model.H:
            model.a["dem_passenger", y, h].fix(True)
            dem_y = cnf.DATA.get_annual("dem_passenger", "actual_demand", y)
            hourly_dem = pass_demand_shape[h] * dem_y / 365
            model.a["dem_passenger", y, h].set_value(hourly_dem)


# --------------------------------------------------------------------------- #
# Pyomo Components
# --------------------------------------------------------------------------- #
def _sets(model: pyo.ConcreteModel):
    """Create sets used by this sector."""
    demands = set(cnf.ENTITIES[cnf.ENTITIES.str.startswith(GROUP_ID)])
    model.Dems = pyo.Set(initialize=demands, ordered=False)
    model.DemsFiE = pyo.Set(
        within=model.F * model.E,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in demands},
    )


def _expressions(model: pyo.ConcreteModel):
    model.dem_e_CostTotal = pyo.Expression(expr=_e_cost_total(model))


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Input
    model.dem_c_flow_in = pyo.Constraint(model.Dems, model.Y, model.D, model.H, rule=gen_con.c_flow_in)
    model.dem_c_input_share_equal = pyo.Constraint(
        model.DemsFiE, model.Y, model.D, model.H, rule=gen_con.c_input_share_equal
    )


def _initialise(model: pyo.ConcreteModel):
    """Set initial sector values."""
    _init_dem_elec(model)
    # _init_dem_passenger(model)


# --------------------------------------------------------------------------- #
# Sector configuration
# --------------------------------------------------------------------------- #
def configure_sector(model):
    """Prepare the sector."""
    _sets(model)
    _expressions(model)
    _constraints(model)
    _initialise(model)
