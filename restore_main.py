# --------------------------------------------------------------------------- #
# Filename: restore_main.py
# Path: /restore_main.py
# Created Date: Thursday, December 8th 2022, 4:36:17 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Main model file."""
from model_utils import initialisation as init
from sectors import electricity
from sectors import trade
from sectors import extraction


model = init.init_model()
trade.configure_sector(model)
electricity.configure_sector(model)
extraction.configure_sector(model)
