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
from model_utils import generic as gen
from gen_utils import k_clustering

GROUP_ID = "dem_"


# --------------------------------------------------------------------------- #
# Sector-specific constraints
# --------------------------------------------------------------------------- #
def _init_dem_elec(model: pyo.ConcreteModel):
    """Electricity demand is taken using K-Means, for now."""
    # Set electricity demand
    elec_demand_y = [cnf.DATA.get_annual("dem_elec", "actual_demand", y) for y in model.Years]
    _, elec_demand_y_h = k_clustering.get_demand_shape(model.Years, [0], elec_demand_y)
    # Convert back into TWh and remove the array shape
    # TODO: move the magic value to the demand file to enable conversion regardless of the setting?
    elec_demand_y_h = {key: value[0] / 1000 for key, value in elec_demand_y_h.items()}

    for y in model.Years:
        for h in model.Hours:
            model.a["dem_elec", y, h].fix(True)
            model.a["dem_elec", y, h].set_value(elec_demand_y_h[y][h])


def _init_dem_passenger(model: pyo.ConcreteModel):
    """Passenger demand uses the demand shape from the STEM model, for now."""
    # Set passenger travel demand
    # TODO: temporary until a standard for load shapes is created
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

    for y in model.Years:
        for h in model.Hours:
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
        within=model.Flows * model.Ents,
        ordered=False,
        initialize={(f, e) for f, e in model.FiE if e in demands},
    )


def _constraints(model: pyo.ConcreteModel):
    """Set sector constraints."""
    # Input
    model.dem_c_flow_in = pyo.Constraint(model.Dems, model.Years, model.Hours, rule=gen.c_flow_in)
    model.dem_c_input_share_equal = pyo.Constraint(
        model.DemsFiE, model.YOpt, model.Hours, rule=gen.c_input_share_equal
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
    _constraints(model)
    _initialise(model)
