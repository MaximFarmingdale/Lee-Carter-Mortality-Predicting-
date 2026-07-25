# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 18:59:45 2026

@author: Maxim
"""
import polars as pl
import numpy as np
import statsmodels as sm
import matplotlib.pyplot as plt
import xlsxwriter 
from statsmodels.tsa.arima.model import ARIMA

female_time_data = pl.read_csv("data/FemaleMortalityByHalfDecade.csv", has_header=True, schema_overrides={"Age": pl.String})
male_time_data = pl.read_csv("data/MaleMortalityByHalfDecade.csv", has_header=True, schema_overrides={"Age": pl.String})

female_time_data = female_time_data.with_columns([
    pl.col("Year").cast(pl.Int32),
    pl.col("Age")
        .str.replace(r"\+", "", literal= False)
        .str.split("-")
        .list.get(0)
        .cast(pl.Int32),
    pl.col("mx").cast(pl.Float64),
    pl.col("mx").log().alias("log_mx")
    ]).filter((pl.col("Age") >= 18))
male_time_data= male_time_data.with_columns([
    pl.col("Year").cast(pl.Int32),
    pl.col("Age")
        .str.replace(r"\+", "", literal= False)
        .str.split("-")
        .list.get(0)
        .cast(pl.Int32),
    pl.col("mx").cast(pl.Float64),
    pl.col("mx").log().alias("log_mx")
    ]).filter((pl.col("Age") >= 18) )
female_time_data_gbyear = (female_time_data
    .with_columns(pl.col("mx").log().alias("log_mx"))
    .group_by("Year")
    .agg(pl.col("log_mx").mean().alias("k_t"))
    .sort("Year")
    )
male_time_data_gbyear = (male_time_data
    .with_columns(pl.col("mx").log().alias("log_mx"))
    .group_by("Year")
    .agg(pl.col("log_mx").mean().alias("k_t"))
    .sort("Year")
    )

def lee_carter(df):
    """
    Estimates the parameters of the Lee-Carter model by using Singular Value Decomposition.
    This is done by setting up the data as a matrix in the format of age as index and year as columns
    and average log mortality as the value,which is the standard format for this model. 
    The data is then center and Singular Value Decomposition is used to estimate age sensitivity (b_x)
    and the mortality index (k_t). These parameters are then normalized.
    
    Parameters
    df: polars.DateFrame
    
    """
    matrix = df.pivot(values ="log_mx", index = "Age", columns = "Year").sort("Age")
    ages = matrix["Age"].to_numpy()
    years = np.array(matrix.columns[1:], dtype=int)
    m = matrix.drop("Age").to_numpy()
    a_x = m.mean(axis = 1)
    #centering matrix
    z = m - a_x[:, None]
    #Singular Value Decomposition
    u,s,vt = np.linalg.svd(z, full_matrices=False)
    #centering b_x and adjusting k_t
    b_x = u[:,0]
    k_t = s[0] * vt[0,:]
    #normalizing b_x
    c = b_x.sum()
    b_x = b_x / c
    k_t = k_t * c
    #centering k_t
    kt_mean = k_t.mean()
    k_t = k_t - kt_mean
    a_x = a_x + b_x * kt_mean
    
    return ages, years, a_x, b_x, k_t
female_ages, female_years, female_a_x, female_b_x, female_k_t = lee_carter(female_time_data)

male_ages, male_years, male_a_x, male_b_x, male_k_t = lee_carter(male_time_data)

forecast_years = 20

def forecast_kt(k_t):
    
    # random walk with drift
    model = ARIMA(k_t, order=(0, 1, 0), trend="t")
    fitted = model.fit()
    
    drift = fitted.params[0]
    sigma = np.sqrt(fitted.params[1])

    np.random.seed(12345)
    num_simulations = 1000
    paths = np.zeros((forecast_years, num_simulations))

    for sim in range(num_simulations):

        current = k_t[-1]

        for t in range(forecast_years):
            #random_shock
            innovation = np.random.normal(0, sigma)

            current = current + drift + innovation

            paths[t, sim] = current

    summary = {
        "p05": np.percentile(paths, 5, axis=1),
        "median": np.median(paths, axis=1),
        "p95": np.percentile(paths, 95, axis=1)
    }
    return paths, summary, fitted
female_paths, female_summary, female_model = forecast_kt(female_k_t)

male_paths, male_summary, male_model = forecast_kt(male_k_t)

last_year = female_years[-1]
future_years = np.arange(last_year +1, last_year + 1 + forecast_years)
def forecast_mortality(a_x, b_x, k_paths):
    log_mx = (
        a_x[:, None, None]
        + b_x[:, None, None] * k_paths[None, :, :]
    )
    mx = np.exp(log_mx)
    return {
        "p05": np.percentile(mx, 5, axis=2),
        "median": np.median(mx, axis=2),
        "p95": np.percentile(mx, 95, axis=2)
    }
mortality_female = forecast_mortality(female_a_x, female_b_x, female_paths)
mortality_male = forecast_mortality(male_a_x, male_b_x, male_paths)
wb = xlsxwriter.Workbook("MortalityExcel.xlsx")
female_historical = pl.DataFrame({
    "Year:": female_years,
    "k_t":female_k_t
    })
male_historical = pl.DataFrame({
    "Year:": male_years,
    "k_t":male_k_t
    })
female_forecast = pl.DataFrame({
    "Year": future_years,
    "Median": female_summary["median"],
    "P05": female_summary["p05"],
    "P95": female_summary["p95"]
    })
male_forecast = pl.DataFrame({
    "Year": future_years,
    "Median": male_summary["median"],
    "P05": male_summary["p05"],
    "P95": male_summary["p95"]
    })
female_historical.write_excel(
    workbook = wb,
    worksheet="Female Historical"
)
male_historical.write_excel(
    workbook = wb,
    worksheet="Male Historical"
)

female_forecast.write_excel(
    workbook = wb,
    worksheet="Female Forecast"
)
male_forecast.write_excel(
    workbook = wb,
    worksheet="Male Forecast"
)
wb.close()