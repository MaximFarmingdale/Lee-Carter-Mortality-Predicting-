# Lee-Carter Mortality Forecasting

## Overview
This project implements the Lee-Carter mortality model to forecast mortality tables by sex using historical data. Historical trends are modeled by using Singular Value Decomposition (SVD), and future mortality is predicted using a random walk with drift model and Monte Carlo simulations.

This project combines advanced statistical modeling with Python and Excel to show the data in an understandable and clear way.

## Libraries Used

polars  
numpy    
statsmodels  
Xlsxwriter  

## Model

Lee-Carter is a statistical model for forecasting mortality that was created by Ronald D. Lee and Lawrence Carter in 1992, and is one of the most used mortality forecasting models. Historical mortality is modeled using this equation:

### The Model Equation
$$\log(m_{x,t}) = a_x + b_x k_t + \varepsilon_{x,t}$$

### Parameter Definitions
* **$m_{x,t}$**: Mortality rate at a specific age ($x$) and year ($t$).
* **$a_x$**: Average log mortality at each age.
* **$b_x$**: Sensitivity of each age to changes in overall mortality.
* **$k_t$**: Overall mortality index over time, modeled using a random walk with drift.
* **$\varepsilon_{x,t}$**: Error term representing historical residuals.

## Data 
The data used is from the [Human Mortality Database](https://www.mortality.org/) it contains the mortality rate for ages 0-110 from 1933 to 2024. The data is 
separated by sex, with two separate tables for each sex used. 

## Analysis
In this stage, the historical data is modeled using the Lee-Carter framework and then used to estimate the next 20 years of mortality data. The forecast is then grouped by year, aggregating by the mortality index **$k_t$**, and is exported to an Excel workbook along with the historical **$k_t$**.
