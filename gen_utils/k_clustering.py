# --------------------------------------------------------------------------- #
# Filename: k_clustering.py
# Created Date: Monday, May 8th 2023, 10:55:29 am
# Author: Ivan Ruiz Manuel
# Email: ivanruizmanuel@gmail.com
# Copyright (C) 2023 Ivan Ruiz Manuel and University of Geneva
# Apache License 2.0
# https://www.apache.org/licenses/LICENSE-2.0
# --------------------------------------------------------------------------- #
"""Contains k means clustering functionality used by the D-EXPANSE model."""
from os import listdir
from os.path import isfile, join

import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples

DATA_FOLDER = "data/zenodo"


def get_k_means_hourly_demand(n_days: int, load_prof_yr: list) -> tuple[np.ndarray, np.ndarray]:
    """Obtain a number of representative daily load profiles using k-means clustering.

    Args:
        n_days (list): list of daily load profiles to obtain
        load_prof_yr (list): matrix with the load profile to analyze

    Returns:
        tuple[np.ndarray, np.ndarray]: ratios and modelled k-means load for the requested number of days
            - Ratio of occurrence for each day (i.e., how many days in the year will have this shape)
            - Matrix of size (n_days, 24) with the combined hourly demand of all representative days
    """
    k_means_model = KMeans(n_clusters=n_days, random_state=0).fit(load_prof_yr)  # Deterministic clustering
    cluster_labels = k_means_model.fit_predict(load_prof_yr)
    hourly_dem = k_means_model.cluster_centers_

    if n_days > 1:
        # The silhouette_score gives the average value for all the samples.
        # This gives a perspective into the density and separation of the formed clusters
        sample_silhouette_values = silhouette_samples(load_prof_yr, cluster_labels)
        size_cluster = np.zeros(n_days)
        for i in range(n_days):
            # get the number of days corresponding to each cluster
            size_cluster[i] = len(sample_silhouette_values[cluster_labels == i])

        cluster_ratios = np.zeros(n_days)
        for i in range(n_days):
            # calculate the % of representation of cluster i in the whole year
            cluster_ratios[i] = size_cluster[i] / sum(size_cluster)
    else:
        # ratio is 100% if only one day was requested
        cluster_ratios = [1]

    return cluster_ratios, hourly_dem


def get_demand_shape(country: str, years: list, days: int, hist_elec_demand: dict) -> tuple[dict, dict]:
    """Get k-means cluster shapes for the electricity demand in certain years."""
    # TODO: this function only works if the day length is 24 hours.
    k_ratio_y_d = dict.fromkeys(years)
    demand_y_d_h = dict.fromkeys(years)

    for y in years:
        # Fetch the load profile, in the order of country (year) -> country (earliest year) -> generic
        try:
            path = f"{DATA_FOLDER}/_profiles/elec_supply/{country}_{y}.csv"
            load_prof = pd.read_csv(path, index_col=0)
            load_prof = load_prof.fillna(method="bfill", axis=1).values
        except FileNotFoundError:
            try:
                path = f"{DATA_FOLDER}/_profiles/elec_supply"
                profiles = [f for f in listdir(path) if isfile(join(path, f)) and country in f]
                earliest_profile = sorted(profiles)[0]
                path = f"{path}/{earliest_profile}"
                load_prof = pd.read_csv(path, index_col=0)
                load_prof = load_prof.fillna(method="bfill", axis=1).values
            except FileNotFoundError:
                load_prof = pd.read_csv(f"{DATA_FOLDER}/_common/GenericLoadProfile.csv")
                load_prof = load_prof[[c for c in load_prof.columns if "SensedHourly" in c]].values

        k_ratio_y_d[y], prof_demand_d_h = get_k_means_hourly_demand(days, load_prof)

        # Apply a correction to the hourly profiles using historical data.
        # Necessary since demand profiles may not be available for every year.
        # TODO: this should be simplified so that the demand profile IN THE FILE is normalized against the yearly total.
        # That way, you just multiply by the yearly total.
        # Since this is not done, there is a slight error because the total is calculated using the rep. days!
        elec_supplied_y = 0
        for d in range(days):
            elec_supplied_y += sum(prof_demand_d_h[d, :]) * 365 * k_ratio_y_d[y][d]  # mistake!
        hist_prof_ratio_y = hist_elec_demand[y] / elec_supplied_y
        demand_y_d_h[y] = prof_demand_d_h * hist_prof_ratio_y

    return k_ratio_y_d, demand_y_d_h
