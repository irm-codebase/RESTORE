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


def get_plt_inverted_legend(axis: plt.Axes):
    """Invert the labels in a matplotlib figure."""
    handles, labels = axis.get_legend_handles_labels()
    return handles[::-1], labels[::-1]
