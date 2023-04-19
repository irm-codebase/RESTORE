# --------------------------------------------------------------------------- #
# Filename: restore_plots.py
# Path: /restore_plots.py
# Created Date: Sunday, January 15th 2023, 12:37:50 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Graph generating utilities for RESTORE."""
import networkx as nx
import pandas as pd
import pyomo.environ as pyo

from model_utils.data_handler import DataHandler
from analysis import fig_tools

fig_tools.plt.rcParams["axes.prop_cycle"] = fig_tools.plt.cycler(color=fig_tools.plt.cm.tab20.colors)


def plot_io_network(*in_out: pd.DataFrame, labels=True):
    """Create a network graph using input/output dataframes.

    Multiindex/column not supported., and must match for all given dataframes.

    Args:
        labels (bool, optional): Whether to include labels in the plot. Defaults to True.
    """
    network_df = pd.DataFrame()
    for i, io_df in enumerate(in_out):
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


def _prettify_area_plot(axis, title):
    axis.set_title(title)
    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, bbox_to_anchor=(1.1, 1.05))
    fig_tools.plt.tight_layout()
    axis.autoscale()


def _add_historical(axis, model: pyo.ConcreteModel, handler: DataHandler, flow: list):
    historical_data = [handler.get_annual(flow, "actual_flow", y) for y in model.Years]
    historical_ref = pd.Series(data=historical_data, index=model.Years, name="Historical total")
    axis = historical_ref.plot.line(ax=axis, color="black", linestyle="-.")
    return axis


def plot_fout(model, handler: DataHandler, flow_ids: list, unit: str = "TWh", historical: str = None):
    """Plot values flowing out of elements at a flow node."""
    columns = sorted({e for flow in flow_ids for f, e in model.FoE if f == flow})
    value_df = pd.DataFrame(index=model.Years, columns=columns, data=0)

    # Gather values
    for flow in flow_ids:
        for f, e in model.FoE:
            if f == flow:
                for y in model.Years:
                    sum_fout = sum(model.fout[f, e, y, h].value for h in model.Hours)
                    value_df.loc[y, e] += sum_fout * model.TPERIOD  # time correction

    # Plotting
    axis = value_df.plot.area(linewidth=0)
    if historical:
        _add_historical(axis, model, handler, historical)

    # Make the plot pretty
    title = f"Modelled: {flow_ids} ({unit})"
    _prettify_area_plot(axis, title)

    return axis


def plot_fin(model, handler: DataHandler, flow_ids: list, unit: str = "TWh", historical: str = None):
    """Plot values flowing into elements at a flow node."""
    columns = sorted({e for flow in flow_ids for f, e in model.FiE if f == flow})
    value_df = pd.DataFrame(index=model.Years, columns=columns, data=0)

    # Gather values
    for f, e in model.FiE:
        if f in flow_ids:
            for y in model.Years:
                sum_fout = sum(model.fin[f, e, y, h].value for h in model.Hours)
                value_df.loc[y, e] += sum_fout * model.TPERIOD  # time correction

    # Plotting
    axis = value_df.plot.area(linewidth=0)
    if historical:
        _add_historical(axis, model, handler, historical)

    # Make the plot pretty
    title = f"Modelled: {flow_ids} ({unit})"
    _prettify_area_plot(axis, title)

    return axis


def plot_ctot(model, handler: DataHandler, grouping: str, unit="GW", use_actual=False):
    """Plot the capacity of the elements in a group."""
    group_ids = [e for e in model.Elems if grouping in e and e in model.Caps]
    cap_df = pd.DataFrame(index=model.Years, columns=group_ids)
    for e in group_ids:
        for y in model.Years:
            if use_actual:
                cap_df.loc[y, e] = handler.get_annual(e, "actual_capacity", y)
            else:
                cap_df.loc[y, e] = model.ctot[e, y].value

    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)

    title = f": Capacity: {grouping} ({unit})"
    title = "Hist. estimates" + title if use_actual else "Modelled" + title

    axis.set_title(f"Net capacity at {grouping} ({unit})")
    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, loc="center left", bbox_to_anchor=(1, 0.5))
    fig_tools.plt.tight_layout()
    axis.autoscale()

    return axis


# TODO: cap_elements should be derived from an input.
def plot_fout_ctot(model, handler: DataHandler, flow: str, unit="GW"):
    """Plot the capacity of the conversion elements feeding into a flow."""
    cap_elements = [e for f, e in model.FoE if f == flow and e in (model.Caps - model.Trades)]
    cap_df = pd.DataFrame(index=model.Years, columns=cap_elements)
    element_actuals = pd.Series(data=0, index=model.Years, name="Aggr. element references")
    for e in cap_elements:
        o_eff = handler.get_const_fxe(e, "output_efficiency", flow)
        for y in model.Years:
            cap_df.loc[y, e] = o_eff * model.ctot[e, y].value
            element_actuals[y] += handler.get_annual(e, "actual_capacity", y) * o_eff

    axis = cap_df.plot(kind="bar", stacked=True, width=0.8)

    # Aggregated historical reference
    # hist_values = [handler.get_annual(flow, "actual_capacity", y) for y in model.Years]
    # historical = pd.Series(data=hist_values, index=model.Years, name="Historical reference")
    # axis = historical.plot(color="black", linestyle="-.", use_index=False, mark_right=False, rot=90)

    # Per-technology 'actual' values
    axis = element_actuals.plot(color="red", use_index=False, mark_right=False, rot=90)

    axis.set_title(f"Net capacity at {flow} ({unit})")
    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, bbox_to_anchor=(1, 1.05))
    fig_tools.plt.tight_layout()
    axis.autoscale()

    return axis


def plot_process_act(model, handler: DataHandler, process, trd_dir=None, axis=None, title: bool = False):
    """Plot activity values at a process element."""
    activity = pd.Series(index=model.Years, name=process)
    if process in model.Trades:
        if trd_dir == "imp":
            act = model.aimp
            value_type = "actual_import"
        elif trd_dir == "exp":
            act = model.aexp
            value_type = "actual_export"
        else:
            raise ValueError("'trd_dir' must be specified as 'imp' or 'exp' for", process)
    else:
        act = model.a
        value_type = "actual_activity"

    for y in model.Years:
        activity[y] = model.TPERIOD * sum(act[process, y, h].value for h in model.Hours)
    axis = activity.plot.line(ax=axis)

    hist_values = [handler.get_annual(process, value_type, y) for y in model.Years]
    actual = pd.Series(data=hist_values, index=model.Years, name="Historical total")
    axis = actual.plot.line(ax=axis, color="black", linestyle="-.")
    if title is not None:
        axis.set_title(process + " (TWh)")
    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, bbox_to_anchor=(1.1, 1.05))
    fig_tools.plt.tight_layout()
    axis.autoscale()

    return axis


def plot_demand(model, demand_id, unit="TWh"):
    """Plot demand trend."""
    annual_demand = pd.Series(index=model.Years, name=demand_id)

    for y in model.Years:
        annual_demand[y] = model.TPERIOD * sum(model.a[demand_id, y, h].value for h in model.Hours)

    axis = annual_demand.plot.line()
    axis.set_title(demand_id + f" ({unit})")

    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, bbox_to_anchor=(1.1, 1.05))
    fig_tools.plt.tight_layout()
    axis.autoscale()

    return axis
