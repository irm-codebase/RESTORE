# --------------------------------------------------------------------------- #
# Filename: model_plots.py
# Created Date: Monday, May 8th 2023, 10:55:29 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Graph generating utilities for RESTORE model outputs."""
import pandas as pd
import pyomo.environ as pyo

from model_utils.data_handler import DataHandler
from plotting import fig_tools


def _add_historical(axis, model: pyo.ConcreteModel, handler: DataHandler, flow: list):
    historical_data = [handler.get_annual(flow, "actual_flow", y) for y in model.YALL]
    historical_ref = pd.Series(data=historical_data, index=model.YALL, name="Historical total")
    axis = historical_ref.plot.line(ax=axis, color="black", linestyle="-.")
    return axis


# --------------------------------------------------------------------------- #
# Flow plots
# --------------------------------------------------------------------------- #
def plot_flow_fout(model, handler: DataHandler, flow_ids: list, unit: str = "TWh", hist: str = None):
    """Plot the modelled entity out flows at a flow node."""
    entity_ids = sorted({e for f, e in model.FoE if f in flow_ids})
    value_df = pd.DataFrame(index=model.YALL, columns=entity_ids, data=0)

    # Gather values
    for f, e in model.FoE:
        if f in flow_ids:
            y = model.Y.first()
            for y_x in model.YALL:
                if y_x in model.Y:
                    y = y_x
                sum_fout = model.e_TotalAnnualOutflow[f, e, y]()
                value_df.loc[y_x, e] += sum_fout  # time correction
    value_df = abs(value_df)  # Get rid of negative near-zero tolerances
    # Plotting
    axis = value_df.plot.area(linewidth=0)
    if hist:
        _add_historical(axis, model, handler, hist)
    title = f"Modelled:flow:{flow_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_flow_fin(model, handler: DataHandler, flow_ids: list, unit: str = "TWh", hist: str = None):
    """Plot the modelled entity in flows at a flow node."""
    entity_ids = sorted({e for f, e in model.FiE if f in flow_ids})
    value_df = pd.DataFrame(index=model.YALL, columns=entity_ids, data=0)

    # Gather values
    for f, e in model.FiE:
        if f in flow_ids:
            y = model.Y.first()
            for y_x in model.YALL:
                if y_x in model.Y:
                    y = y_x
                sum_fin = model.e_TotalAnnualInflow[f, e, y]()
                value_df.loc[y_x, e] += sum_fin  # time correction
    value_df = abs(value_df)  # Get rid of negative near-zero tolerances
    # Plotting
    axis = value_df.plot.area(linewidth=0)
    if hist:
        _add_historical(axis, model, handler, hist)
    title = f"Modelled:Input:{flow_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


# --------------------------------------------------------------------------- #
# Group plots
# --------------------------------------------------------------------------- #
def plot_group_ctot(model, group_ids: list, unit="GW"):
    """Plot the modelled total capacity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e and e in model.Caps})
    cap_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            cap_df.loc[y, e] = model.ctot[e, y].value

    # Plotting
    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)
    title = f"Modelled:Tot Cap.:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_group_cnew(model, group_ids: list, unit="GW"):
    """Plot the modelled new capacity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e and e in model.Caps})
    cap_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            cap_df.loc[y, e] = model.cnew[e, y].value

    # Plotting
    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)
    title = f"Modelled:New Cap.:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_group_cret(model, group_ids: list, unit="GW"):
    """Plot the modelled retired capacity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e and e in model.Caps})
    cap_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            cap_df.loc[y, e] = model.cret[e, y].value

    # Plotting
    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)
    title = f"Modelled:New Cap.:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_group_act(model, group_ids: list, unit="GW"):
    """Plot the activity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e})
    act_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            act_df.loc[y, e] = sum(model.DL[y, d]() * model.a[e, y, d, h].value for d in model.D for h in model.H)

    # Plotting
    axis = act_df.plot.area(linewidth=0)
    title = f"Modelled:Activity:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_act(model, entity_id, unit="GW"):
    """Plot the activity of a single entity."""
    act = [model.e_TotalAnnualActivity[entity_id, y]() for y in model.Y]
    act_df = pd.Series(index=model.Y, name=entity_id, data=act)

    # Plotting
    axis = act_df.plot.area(linewidth=0)
    title = f"Modelled:Activity:{entity_id}"
    fig_tools.prettify_plot(axis, title, unit)
