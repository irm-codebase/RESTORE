# --------------------------------------------------------------------------- #
# Filename: configuration.py
# Path: /configuration.py
# Created Date: Friday, March 10th 2023, 2:24:16 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2023 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Centralised configuration file for the model.

Shall be used by all generic and project-specific model modules.

Rules:
- Holds all data and model parameters declared as CONSTANTS.
- Only include things that apply to all modules. Specifics go in sector files.
- No function declarations, not even generic ones.
"""
import pandas as pd
import numpy as np

from model_utils import data_handler as _handler

ISO2 = "CH"
ISO3 = "CHE"

# Build model configuration
DATA = _handler.DataHandler("data/cnf_files/test.xlsx")
ENTITIES = pd.merge(DATA.fxe["FiE"], DATA.fxe["FoE"], how='outer', left_index=True, right_index=True).index
FLOWS = set(pd.merge(DATA.fxe["FiE"], DATA.fxe["FoE"], how='inner').columns)

# User defined parameters
NDAYS = 2
YEARSLICE = 1
TIMESLICE = 1
YEARS = np.arange(1990, 2020, YEARSLICE)
DAYS = np.arange(NDAYS)
HOURS = np.arange(0, 24, TIMESLICE)
