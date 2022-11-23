# --------------------------------------------------------------------------- #
# Filename: unit_conv.py
# Path: /unit_conv.py
# Created Date: Tuesday, November 15th 2022, 4:16:59 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Provides basic unit conversion functions in one place."""


def tj_to_gwh(num):
    """Convert TJ to GWh."""
    return num * 1/3.6


def gwh_to_tj(num):
    """Convert GWh to TJ."""
    return num * 3.6
