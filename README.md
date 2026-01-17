# Time Series Forecasting and Evaluation System

## Overview
This project provides a complete system for time series forecasting and evaluation using multiple forecasting models. It includes functionality to fetch and preprocess time series data stored in an SQLite database, generate forecasts using different models (ARIMA, SARIMA, XGBoost, Random Forest), evaluate forecasting performance with common metrics, and generate exploratory data analysis (EDA) plots with stationarity testing.

## Features
- Fetch time series data from a SQLite database where data is stored as JSON in a table.
- Preprocess time series data including timestamp handling and numeric conversion.
- Generate forecasts using:
  - ARIMA
  - SARIMA (seasonal ARIMA)
  - XGBoost Regressor with lag features
  - Random Forest Regressor with lag features
- Evaluate model forecasts using MAE (Mean Absolute Error), RMSE (Root Mean Squared Error), and MAPE (Mean Absolute Percentage Error).
- Rank models based on forecast accuracy metrics.
- Generate EDA plots including:
  - Time series line plot
  - Trend, seasonality, and cyclic components decomposition
  - Moving average trend plot
  - Heatmaps of dependent variable aggregated by time windows (weekly/hourly)
- Perform Augmented Dickey-Fuller test to check stationarity of series.
- Logging with various levels (INFO, WARNING, ERROR) for debugging and operational transparency.
- Use of a non-interactive matplotlib backend for compatibility with Flask or similar web frameworks.

## Requirements
- Python libraries: pandas, numpy, sqlite3, json, logging, matplotlib, seaborn, statsmodels, xgboost, scikit-learn
- SQLite database (`data_storage.db`) with a `timeseries_data` table having columns:
  - `dataset_name` (string)
  - `timestamp` (datetime string)
  - `data` (JSON string containing the time series data dictionary)

## Components

### Data Fetching and Preprocessing
- Connects to SQLite and reads timestamps and JSON data.
- Expands JSON data into DataFrame columns.
- Converts timestamps to datetime and dependent variable to numeric.
- Handles data cleaning such as removing NaNs and sorting by timestamp.

### Forecast Models
- **ARIMA** and **SARIMA**: Classical statistical time series models with configurable order and seasonal order.
- **XGBoost** and **Random Forest**: Machine learning approaches using historic lagged values as features for regression.

### Evaluation
- Fetches actual recent values (last 10 steps by default) for comparison.
- Calculates MAE, RMSE, and MAPE metrics.
- Handles mismatched lengths and errors gracefully.
- Ranks models by metric values.

### EDA and Stationarity Testing
- Generates plots for time series visualization and insights.
- Performs seasonal decomposition into trend, seasonal, and residual components.
- Produces moving average plot for trend smoothing.
- Creates heatmaps based on chosen time aggregations.
- Runs Augmented Dickey-Fuller test to assess if the series is stationary.

## Logging and Debugging
- Logs stored in `evaluators.log` for evaluation process.
- Logs stored in `eda.log` for exploratory data analysis.
- Debug prints help trace data handling and model forecasting steps.

## Notes
- Forecast steps default to 10 but can be adjusted in the code.
- Make sure sufficient data exists in the database for models to run effectively.
- The forecasting models may require tuning of parameters for specific datasets.
