# --------------------------------------------------------------------------- #
# Filename: data_plots.py
# Path: /data_plots.py
# Created Date: Tuesday, May 2nd 2023, 4:07:19 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Graph generating utilities for model data."""
import networkx as nx
import pandas as pd
from pyomo.environ import ConcreteModel

from model_utils.data_handler import DataHandler
from plotting import fig_tools


def plot_io_network(handler: DataHandler, labels=True):
    """Create a network graph using input/output dataframes.

    Multiindex/column not supported., and must match for all given dataframes.

    Args:
        labels (bool, optional): Whether to include labels in the plot. Defaults to True.
    """
    # TODO: Fix missing entities
    # TODO: add colours?
    # TODO: fix labels?
    in_flow_df = handler.fxe["FiE"]
    out_flow_df = handler.fxe["FoE"]
    network_df = pd.DataFrame()
    for i, io_df in enumerate([in_flow_df, out_flow_df]):
        if i == 0:
            network_df = io_df.copy()
        else:
            network_df.update(io_df)
    edges = network_df.index.to_list() + network_df.columns.to_list()
    adjacency_df = pd.DataFrame(index=edges, columns=edges, dtype=float)
    adjacency_df.update(network_df)
    adjacency_df = adjacency_df.notnull().astype(int)
    network = nx.from_pandas_adjacency(adjacency_df)
    nx.draw_networkx(network, node_size=100, font_size=6, with_labels=labels)


# --------------------------------------------------------------------------- #
# Flow plots
# --------------------------------------------------------------------------- #
def plot_flow_fout(model, handler: DataHandler, flow_ids: list, unit: str = "TWh"):
    """Plot the historical entity outflows at a flow node.

    TODO: may not work properly for entities with multiple output efficiencies. Add a warning?
    """
    entity_ids = sorted({e for f, e in model.FoE if f in flow_ids})
    value_df = pd.DataFrame(index=model.Y, columns=entity_ids, data=0)

    # Gather values
    for f in flow_ids:
        for e in entity_ids:
            for y in model.Y:
                if e in model.Trades:
                    activity = handler.get_annual(e, "actual_import", y)
                else:
                    activity = handler.get_annual(e, "actual_activity", y)
                efficiency = handler.get_fxe(e, "output_efficiency", f, y)
                value_df.loc[y, e] = activity * efficiency
    # Plotting
    axis = value_df.plot.area(linewidth=0)
    title = f"Hist. estimate:fout:{flow_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_flow_fin(model: ConcreteModel, handler: DataHandler, flow_ids: list, unit: str = "TWh"):
    """Plot the historical entity inflows at a flow node.

    TODO: may not work properly for entities with multiple input efficiencies. Add a warning?
    """
    entity_ids = sorted({e for f, e in model.FiE if f in flow_ids})
    value_df = pd.DataFrame(index=model.Y, columns=entity_ids, data=0)

    # Gather values
    for f in flow_ids:
        for e in entity_ids:
            for y in model.Y:
                if e in model.Trades:
                    activity = handler.get_annual(e, "actual_export", y)
                else:
                    activity = handler.get_annual(e, "actual_activity", y)
                efficiency = handler.get_fxe(e, "input_efficiency", f, y)
                value_df.loc[y, e] = activity * efficiency
    # Plotting
    axis = value_df.plot.area(linewidth=0)
    title = f"Hist. estimate:fout:{flow_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


# --------------------------------------------------------------------------- #
# Group plots
# --------------------------------------------------------------------------- #
def plot_group_param(model: ConcreteModel, handler: DataHandler, param: str, group_ids: list, unit: str):
    """Plot the historical new capacity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e and e in model.Caps})
    param_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        param_df[e] = {y: handler.get_annual(e, param, y) for y in model.Y}

    # Plotting
    axis = param_df.plot(kind="bar", stacked=True, width=0.8)
    title = f"Modelled:Tot Cap.:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_group_ctot(model: ConcreteModel, handler: DataHandler, group_ids: list, unit="GW"):
    """Plot the historical new capacity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e and e in model.Caps})
    cap_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            cap_df.loc[y, e] = handler.get_annual(e, "actual_capacity", y)

    # Plotting
    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)
    title = f"Modelled:Tot Cap.:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_group_cnew(model: ConcreteModel, handler: DataHandler, group_ids: list, unit="GW"):
    """Plot the historical new capacity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e and e in model.Caps})
    cap_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            cap_df.loc[y, e] = handler.get_annual(e, "actual_new_capacity", y)

    # Plotting
    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)
    title = f"Modelled:New Cap.:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_group_cret(model: ConcreteModel, handler: DataHandler, group_ids: list, unit="GW"):
    """Plot the historical retired capacity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e and e in model.Caps})
    cap_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            cap_df.loc[y, e] = handler.get_annual(e, "actual_retired_capacity", y)

    # Plotting
    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)
    title = f"Modelled:Ret Cap.:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis


def plot_group_act(model: ConcreteModel, handler: DataHandler, group_ids: list, unit="GW"):
    """Plot the activity of the entities in a group."""
    entity_ids = sorted({e for group in group_ids for e in model.E if group in e})
    act_df = pd.DataFrame(index=model.Y, columns=entity_ids)

    # Gather values
    for e in entity_ids:
        for y in model.Y:
            act_df.loc[y, e] = handler.get_annual(e, "actual_activity", y)

    # Plotting
    axis = act_df.plot.area(linewidth=0)
    title = f"Modelled:Activity:{group_ids}"
    fig_tools.prettify_plot(axis, title, unit)

    return axis
