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

from gen_utils.cnf_tools import ConfigHandler
from gen_utils import fig_tools

fig_tools.plt.rcParams['axes.prop_cycle'] = fig_tools.plt.cycler(color=fig_tools.plt.cm.tab20c.colors)


def plot_io_network(*in_out: pd.DataFrame, labels=True):
    """Create a network graph using input/output dataframes.

    Multiindex/column not supported., and must match for all given dataframes.

    Args:
        labels (bool, optional): Whether to include labels in the plot. Defaults to True.
    """
    io_df = pd.DataFrame()
    for i, df in enumerate(in_out):
        if i == 0:
            io_df = df.copy()
        else:
            io_df.update(df)

    edges = io_df.index.to_list() + io_df.columns.to_list()
    adjacency_df = pd.DataFrame(index=edges, columns=edges, dtype=float)
    adjacency_df.update(io_df)
    adjacency_df = adjacency_df.notnull().astype(int)
    network = nx.from_pandas_adjacency(adjacency_df)
    nx.draw_networkx(network, node_size=100, font_size=6, with_labels=labels)


def plot_fout(model, handler: ConfigHandler, flow):
    """Plot values flowing out of elements at a flow node."""
    columns = [e for f, e in model.FoE if f == flow]
    fout_df = pd.DataFrame(index=model.Years, columns=columns)
    for f, e in model.FoE:
        if f == flow:
            for y in model.Years:
                fout_df.loc[y, e] = model.TPERIOD * sum(model.fout[f, e, y, h].value for h in model.Hours)

    axis = fout_df.plot.area(linewidth=0)

    hist_values = [handler.get_flow_value(flow, "actual_flow", y) for y in model.Years]
    actual = pd.Series(data=hist_values, index=model.Years, name="Historical total")
    axis = actual.plot.line(ax=axis, color="black", linestyle="-.")
    axis.set_title(f"FoE at {flow}")
    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, bbox_to_anchor=(1.1, 1.05))
    fig_tools.plt.tight_layout()
    axis.autoscale()

    return axis


def plot_fin(model, handler: ConfigHandler, flow):
    """Plot values flowing into elements at a flow node."""
    columns = [e for f, e in model.FiE if f == flow]
    fin_df = pd.DataFrame(index=model.Years, columns=columns)
    for f, e in model.FiE:
        if f == flow:
            for y in model.Years:
                fin_df.loc[y, e] = model.TPERIOD * sum(model.fin[f, e, y, h].value for h in model.Hours)

    axis = fin_df.plot.area(linewidth=0)

    hist_values = [handler.get_flow_value(flow, "actual_flow", y) for y in model.Years]
    actual = pd.Series(data=hist_values, index=model.Years, name="Historical total")
    axis = actual.plot.line(ax=axis, color="black", linestyle="-.")
    axis.set_title(f"FiE at {flow}")
    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, bbox_to_anchor=(1.1, 1.05))
    fig_tools.plt.tight_layout()
    axis.autoscale()

    return axis


def plot_process_act(model, handler: ConfigHandler, process, trd_dir=None, axis=None, title: bool = False):
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

    hist_values = [handler.get_process_value(process, value_type, y) for y in model.Years]
    actual = pd.Series(data=hist_values, index=model.Years, name="Historical total")
    axis = actual.plot.line(ax=axis, color="black", linestyle="-.")
    if title is not None:
        axis.set_title(process)
    handles, labels = fig_tools.get_plt_inverted_legend(axis)
    axis.legend(handles, labels, bbox_to_anchor=(1.1, 1.05))
    fig_tools.plt.tight_layout()
    axis.autoscale()

    return axis
