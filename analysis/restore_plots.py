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
