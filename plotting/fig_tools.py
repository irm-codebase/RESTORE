# --------------------------------------------------------------------------- #
# Filename: fig_tools.py
# Path: /fig_tools.py
# Created Date: Tuesday, January 24th 2023, 5:21:12 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Simple fixes for plotting.

Stick to generic functionality, do not put result-specific stuff in here.
"""
import matplotlib.pyplot as plt

# Configure plot settings
plt.rcParams["axes.prop_cycle"] = plt.cycler(color=plt.cm.tab20.colors)


def inverted_legend(axis: plt.Axes, bbox_to_anchor=(1.05, 0.5)):
    """Invert the labels in a matplotlib figure."""
    handles, labels = axis.get_legend_handles_labels()
    axis.legend(handles[::-1], labels[::-1], bbox_to_anchor=bbox_to_anchor, loc="center left")


def prettify_plot(axis: plt.Axes, title: str, label: str):
    """Make plot prettier by adding a legend, title and sorting the labels."""
    axis.set_title(title)
    axis.set_ylabel(label)
    inverted_legend(axis)
    plt.tight_layout()
    axis.autoscale()
