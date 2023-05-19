# --------------------------------------------------------------------------- #
# Filename: file_manager.py
# Created Date: Monday, May 8th 2023, 10:55:29 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Used for generic parsing utility functions."""
import os
from datetime import datetime

import pandas as pd

TEMPLATE_PATH = "data/zenodo/_templates/template.xlsx"
COLUMNS = pd.read_excel(TEMPLATE_PATH, sheet_name="template", header=4).columns


def save_csv(csv_df: pd.DataFrame, path: str) -> None:
    """Save the csv file, adding metadata.

    Args:
        csv_df (pd.DataFrame): dataframe.
        path (str): directory where the data should be saved.
    """
    filename = csv_df.loc[0, "Country"] + "_" + csv_df.loc[0, "Entity"] + ".xlsx"
    if not os.path.exists(path):
        os.makedirs(path)
    elif os.path.exists(path + filename):
        os.remove(path + filename)

    with open(path + filename, "a", encoding="utf-8") as file:
        file.write(f"Name: {filename}\n")
        date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"Date: {date}\n")
        file.write("Author: Ivan Ruiz Manuel\n\n")
        csv_df.to_csv(file, header=False)


def save_excel(dataframe: pd.DataFrame, folder_path: str, append_country_code=False):
    """Save a RESTORE data file as .xlsx, adding metadata and ensuring correct cell types.

    Args:
        dataframe (pd.DataFrame): dataframe
        folder_path (str): folder to save
    """
    filename = dataframe.loc[0, "Entity"] + ".xlsx"
    if append_country_code:
        filename = dataframe.loc[0, "Country"] + filename

    # Prepare file location
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    elif os.path.exists(folder_path + filename):
        os.remove(folder_path + filename)

    writer = pd.ExcelWriter(  # pylint: disable=abstract-class-instantiated
        os.path.join(folder_path, filename),
        engine="xlsxwriter",
        engine_kwargs={"options": {"strings_to_numbers": True}},
    )

    metadata = pd.DataFrame(columns=["Data"])
    metadata.loc["Name:"] = filename
    metadata.loc["Date:"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    metadata.loc["Author:"] = "Ivan Ruiz Manuel"

    with writer:
        metadata.to_excel(writer, header=False)
        dataframe.to_excel(writer, index=False, startrow=4)


def get_template_dataframe() -> pd.DataFrame:
    """Get an empty template dataframe with the new Zenodo configuration.

    Returns:
        pd.Dataframe: empty dataframe.
    """
    empty_df = pd.read_excel(TEMPLATE_PATH, sheet_name="template", header=4)
    return empty_df
