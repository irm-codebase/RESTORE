# --------------------------------------------------------------------------- #
# Filename: fig_tools.py
# Created Date: Monday, May 8th 2023, 10:55:29 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
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
