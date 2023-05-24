# --------------------------------------------------------------------------- #
# Filename: configuration.py
# Created Date: Tuesday, May 16th 2023, 5:39:39 pm
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
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
YEARSLICE = 1
NDAYS = 4
TIMESLICE = 3
YEARS = np.arange(1990, 2020, YEARSLICE)
DAYS = np.arange(NDAYS)
HOURS = np.arange(0, 24, TIMESLICE)
