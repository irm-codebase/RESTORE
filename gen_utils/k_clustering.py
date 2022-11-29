# --------------------------------------------------------------------------- #
# Filename: k_clustering.py
# Path: /k_clustering.py
# Created Date: Tuesday, November 8th 2022, 10:47:58 am
# Author: Xin Wen, Ivan Ruiz Manuel
# Copyright (c) 2022 University of Geneva
# GNU General Public License v3.0 or later
# https://www.gnu.org/licenses/gpl-3.0-standalone.html
# --------------------------------------------------------------------------- #
"""Contains k means clustering functionality used by the D-EXPANSE model."""
from os import listdir
from os.path import isfile, join

import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples


def get_k_means_hourly_demand(days: list, load_prof_yr: list) -> tuple[np.ndarray, np.ndarray]:
    """Obtain a number of representative daily load profiles using k-means clustering.

    Args:
        n_days (list): list of daily load profiles to obtain
        load_prof_yr (list): matrix with the load profile to analyze

    Returns:
        tuple[np.ndarray, np.ndarray]: ratios and modelled k-means load for the requested number of days
            - Ratio of occurrence for each day (i.e., how many days in the year will have this shape)
            - Matrix of size (n_days, 24) with the combined hourly demand of all representative days
    """
    k_means_model = KMeans(n_clusters=len(days), random_state=0).fit(load_prof_yr)
    cluster_labels = k_means_model.fit_predict(load_prof_yr)
    hourly_dem = k_means_model.cluster_centers_ / 1000

    # The silhouette_score gives the average value for all the samples.
    # This gives a perspective into the density and separation of the formed clusters
    sample_silhouette_values = silhouette_samples(load_prof_yr, cluster_labels)
    size_cluster = np.zeros(len(days))
    for i in days:
        # get the number of days corresponding to each cluster
        size_cluster[i] = len(sample_silhouette_values[cluster_labels == i])

    cluster_ratios = np.zeros(len(days))
    for i in days:
        # calculate the % of representation of cluster i in the whole year
        cluster_ratios[i] = size_cluster[i] / sum(size_cluster)

    return cluster_ratios, hourly_dem


def get_supplied_ratio_y_d(demand_y_d_h: dict, k_ratio_y_d: dict, days: list, year: int) -> list:
    """Obtain the total energy supplied by each representative day in a year.

    Args:
        demand_y_d_h (dict): Demand profile in [year, day, hour]
        k_ratio_y_d (dict): Distribution of representative day in [year day]
        days (list): list of representative days
        year (int): year for which the total energy supplied per day will be obtained.

    Returns:
        (list): Amount of energy supplied in each representative day, per year.
    """
    # Get cumulative demand of each representative day in a year (accounting for occurrence).
    demand_d = np.zeros(len(days))
    for d in days:
        demand_d[d] = sum(demand_y_d_h[year][d]) * 365 * k_ratio_y_d[year][d] / 1000

    # Get the total yearly demand of each representative day
    ratio_total_supplied_y_d = np.zeros(len(days))
    for d in days:
        ratio_total_supplied_y_d[d] = demand_d[d] / sum(demand_d)
    return ratio_total_supplied_y_d


def get_demand_shape(years: list, days: list, hist_elec_demand: pd.Series) -> tuple[dict, dict]:
    """Get k-means cluster shapes for the electricity demand in certain years.

    Args:
        years (list): list of years to obtain.
        days (list): list of representative days within a year.
        hist_elec_demand (pd.Series): list of actual historical electricity demand (used for fitting)

    Returns:
        tuple[dict, dict]: [ratio of each representative (year,day), demand shape (year,day,hour)]
    """
    k_ratio_y_d = dict.fromkeys(years)
    demand_y_d_h = dict.fromkeys(years)

    country = "CHE"
    for y in years:
        try:
            path = f"data/zenodo/Electric/Profiles/{country}_{y}.csv"
            load_prof = pd.read_csv(path, index_col=0)
            load_prof = load_prof.fillna(method="bfill", axis=1).values
        except FileNotFoundError:
            try:
                path = "data/zenodo/Electric/Profiles/"
                profiles = [f for f in listdir(path) if isfile(join(path, f)) and country in f]
                earliest_profile = sorted(profiles)[0]
                path = f"data/zenodo/Electric/Profiles/{earliest_profile}"
                load_prof = pd.read_csv(path, index_col=0)
                load_prof = load_prof.fillna(method="bfill", axis=1).values
            except FileNotFoundError:
                load_prof = pd.read_csv("data/zenodo/Electric/_common/GenericLoadProfile.csv")
                load_prof = load_prof[[i for i in load_prof.columns if "SensedHourly" in i]].values

        k_ratio_y_d[y], prof_demand_d_h = get_k_means_hourly_demand(days, load_prof)

        # Apply a correction to the hourly profiles using historical data.
        # Necessary since demand profiles may not be available for every year.
        elec_supplied_y = 0
        for i in days:
            elec_supplied_y += sum(prof_demand_d_h[i, :]) * 365 * k_ratio_y_d[y][i] / 1000
        hist_prof_ratio_y = hist_elec_demand[y] / elec_supplied_y
        demand_y_d_h[y] = prof_demand_d_h * hist_prof_ratio_y

    return k_ratio_y_d, demand_y_d_h
