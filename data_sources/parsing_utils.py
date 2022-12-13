# --------------------------------------------------------------------------- #
# Filename: parsing_utils.py
# Path: /parsing_utils.py
# Created Date: Monday, December 12th 2022, 4:34:03 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Used for generic parsing utility functions."""

import os
from datetime import datetime

import pandas as pd


def save_csv(csv_df: pd.DataFrame, path: str, filename: str) -> None:
    """Save the csv file, adding metadata.

    Args:
        csv_df (pd.DataFrame): dataframe.
        path (str): directory where the data should be saved.
        filename (str): name of the file.
    """
    if not os.path.exists(path):
        os.makedirs(path)
    elif os.path.exists(path + filename):
        os.remove(path + filename)

    with open(path + filename, "a", encoding="utf-8") as file:
        file.write(f"Name: {filename}\n")
        file.write(f"Date: {datetime.now()}\n")
        file.write("Author: Ivan Ruiz Manuel\n\n")
        csv_df.to_csv(file, header=False)


def get_template_dataframe() -> pd.DataFrame:
    """Get an empty template dataframe with the new Zenodo configuration.

    Returns:
        pd.Dataframe: empty dataframe.
    """
    path = "data_sources/zenodo_ivan/_templates/template.csv"
    empty_df = pd.read_csv(path, header=4)
    return empty_df
