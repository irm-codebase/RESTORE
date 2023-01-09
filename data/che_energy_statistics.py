# --------------------------------------------------------------------------- #
# Filename: che_energy_statistics.py
# Path: /che_energy_statistics.py
# Created Date: Tuesday, November 15th 2022, 3:55:22 pm
# Author: Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Extracts energy data from the swiss Total Energy Statistics Excel.

Data taken from the Swiss Federal Statistical Office:
https://www.bfe.admin.ch/bfe/en/home/supply/statistics-and-geodata/energy-statistics/overall-energy-statistics.html/
"""
import numpy as np
import pandas as pd

from parsing_utils import save_csv


class CHEParser:
    """Extracts info from the energy balance file and creates a .csv file in the standard style."""

    COUNTRY = "CHE"
    ENTITY = "Country"
    TEMPLATE_PATH = "data/_templates/template.csv"
    TEMPLATE_ROW = 4
    IN_PATH = "data/sources/CHE/7519-GEST_2021_Tabellen.xlsx"
    OUT_PATH = f"data/DExpanse/{COUNTRY}/"
    REFERENCE = "Swiss overall energy statistics 2021"

    def __init__(self, years=(1990, 2019)) -> None:
        """Create parser object.

        Args:
            years (tuple, optional): That should be parsed. Defaults to (1990, 2019).
        """
        self.years = list(range(years[0], years[1] + 1))

    def get_df_from_sheet(self, sheet_name: str, index_col=0, header=5) -> pd.DataFrame:
        """Get a pandas dataframe from the document.

        Args:
            sheet_name (str): sheet name
            index_col (int, optional): location of the years, for indexing. Defaults to 0.
            header (int, optional): row(s) to use as header(s) beginning at 0. Must be list if several.
                                    Defaults to 5.

        Returns:
            pd.DataFrame: resulting dataframe, may have multi-index.
        """
        sheet = pd.read_excel(self.IN_PATH, sheet_name=sheet_name, index_col=index_col, header=header)
        sheet = sheet[sheet.index.isin(self.years)]  # Obtain the configured years
        sheet = sheet.replace("-", np.nan)
        return sheet

    @staticmethod
    def isconsecutive(lst):
        """Return True if all numbers in lst can be ordered consecutively, and False otherwise."""
        if len(set(lst)) == len(lst) and max(lst) - min(lst) == len(lst) - 1:
            return True
        return False

    def get_column_data(self, sheet: pd.DataFrame, header_arr: list[str]) -> pd.Series:
        """Extract column data using the specified headers.

        Args:
            sheet (pd.DataFrame): dataframe for a sheet
            header_arr (list): headers as seen in the document

        Raises:
            ValueError: sporadic missing values
            ValueError: missing data found after valid data
            ValueError: incorrect dtype in resulting column (not float)

        Returns:
            pd.Series: requested column as a pandas series with index in years.
        """
        # Dig into the dataframe
        data = sheet
        for col in header_arr:
            try:
                data = data[col]
            except KeyError as exc:
                # compress the columns if there are Unknowns
                for i in data.columns:
                    if col in str(i):
                        if "Unnamed" in str(i[0]):
                            data = data[i[0]][col]
                            break
                else:
                    raise KeyError("Mapping key not found:", col) from exc

        # Verification
        null_val = data[data.isnull().tolist()]
        if len(null_val) > 0:
            if not self.isconsecutive(null_val.index):
                raise ValueError("Sporadic missing data in column. Verify column.")
            if data.first_valid_index() < null_val.index[0]:
                raise ValueError("Missing data detected after valid values. Verify column.")
        if not np.issubsctype(data, float):
            raise ValueError("Column dtype did not return as float. Verify column.")
        return data

    def set_csv_data(
        self,
        data: pd.Series,
        csv_df: pd.DataFrame,
        entity: str,
        param_name: str,
        unit=np.nan,
        note=np.nan,
        first=False,
    ) -> pd.DataFrame:
        """Construct a standard database following the format given by Marc.

        Args:
            data (pd.Series): excel data.
            csv_df (pd.DataFrame): dataframe where the data will be stored. Must have the standard columns.
            entity (str): type of file.
            param_name (str): name of the parameter being saved.
            unit (_type_, optional): units of the parameter. Defaults to np.nan.
            note (_type_, optional): additional note. Defaults to np.nan.
            first (bool, optional): if this is the first run of the constructor. Defaults to False.

        Returns:
            pd.DataFrame: in standard Marc format.
        """
        buffer = pd.DataFrame(index=data.index, columns=csv_df.columns)
        buffer["Country"] = self.COUNTRY
        buffer["Entity"] = entity
        buffer["Parameter"] = param_name
        buffer["Year"] = data.index
        buffer["Value"] = data.values
        buffer["Unit"] = unit
        buffer["Reference"] = self.REFERENCE
        buffer["Note"] = note

        if first:
            return buffer
        return pd.concat([csv_df, buffer], ignore_index=True)

    def parse_transport_data(self):
        """Obtain country data for the transport sector."""
        # TODO: this should use the template
        unit = "TJ"
        sheet_name = "T17e"

        sheet = self.get_df_from_sheet(sheet_name, header=[8, 9, 10])
        template_df = pd.read_csv(self.TEMPLATE_PATH, header=self.TEMPLATE_ROW)

        total_fuel = self.get_column_data(sheet, ["Produits pétroliers1", "Total Carburants", unit])
        total_elec = self.get_column_data(sheet, ["Electricité2", "Total Electricité", unit])
        total_biofuel = self.get_column_data(sheet, ["Autres énergies renouvelables6", unit])

        note = "Table " + sheet_name
        entity = self.ENTITY + "Transport"
        param_name = "FinalConsumptionFuel_transport"
        csv_df = self.set_csv_data(total_fuel, template_df, entity, param_name, unit, note, first=True)
        param_name = "FinalConsumptionBioFuel_transport"
        csv_df = self.set_csv_data(total_biofuel, csv_df, entity, param_name, unit, note)
        param_name = "FinalConsumptionElec_transport"
        csv_df = self.set_csv_data(total_elec, csv_df, entity, param_name, unit, note)

        outpath = self.OUT_PATH + "Transport/"
        save_csv(csv_df, outpath)


if __name__ == "__main__":
    test = CHEParser()
    test.parse_transport_data()
