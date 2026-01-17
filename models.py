import os
import numpy as np
import pandas as pd
import sqlite3
import json
import logging
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor

# ---------------------- CONFIG ----------------------
logging.basicConfig(level=logging.INFO)
DATABASE_NAME = "data_storage.db"


# ---------------------- FETCH DATA ----------------------
def fetch_data(dataset_name, dependent_col):
    """Fetch dataset from SQLite and preprocess it."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        query = "SELECT timestamp, data FROM timeseries_data WHERE dataset_name = ?"
        df = pd.read_sql_query(query, conn, params=(dataset_name,))
        conn.close()

        if df.empty:
            logging.warning(f"No data found for dataset '{dataset_name}'.")
            return pd.DataFrame()

        df["data"] = df["data"].apply(json.loads)
        data_expanded = pd.json_normalize(df["data"])
        df = df.drop(columns=["data"]).join(data_expanded)

        if dependent_col not in df.columns:
            logging.error(f"Column '{dependent_col}' not found.")
            return pd.DataFrame()

        df[dependent_col] = pd.to_numeric(df[dependent_col], errors="coerce")
        df.dropna(subset=[dependent_col], inplace=True)

        return df[[dependent_col]].reset_index(drop=True)

    except Exception as e:
        logging.error(f"Database error: {e}")
        return pd.DataFrame()


# ---------------------- ARIMA ----------------------
def arima_forecast(df, dependent_col, steps=10):
    try:
        print("\n🚀 Running ARIMA Forecast")
        model = ARIMA(df[dependent_col], order=(5, 1, 0))
        model_fit = model.fit()

        forecast = model_fit.get_forecast(steps=steps)
        conf_int = forecast.conf_int()

        return [
            {
                "forecast": float(forecast.predicted_mean.iloc[i]),
                "lower_conf_int": float(conf_int.iloc[i, 0]),
                "upper_conf_int": float(conf_int.iloc[i, 1])
            } for i in range(steps)
        ]

    except Exception as e:
        logging.error(f"ARIMA error: {e}")
        return {"error": "ARIMA failed"}


# ---------------------- SARIMA ----------------------
def sarima_forecast(df, dependent_col, steps=10):
    try:
        print("\n🚀 Running SARIMA Forecast")
        model = SARIMAX(df[dependent_col], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        model_fit = model.fit(disp=False)

        forecast = model_fit.get_forecast(steps=steps)
        conf_int = forecast.conf_int()

        return [
            {
                "forecast": float(forecast.predicted_mean.iloc[i]),
                "lower_conf_int": float(conf_int.iloc[i, 0]),
                "upper_conf_int": float(conf_int.iloc[i, 1])
            } for i in range(steps)
        ]

    except Exception as e:
        logging.error(f"SARIMA error: {e}")
        return {"error": "SARIMA failed"}


# ---------------------- XGBOOST ----------------------
def xgboost_forecast(df, dependent_col, steps=10, lag=10):
    try:
        print("\n🚀 Running XGBoost Forecast")
        data = df[dependent_col].values
        X, y = [], []

        for i in range(lag, len(data)):
            X.append(data[i-lag:i])
            y.append(data[i])

        if len(X) == 0:
            return {"error": "Not enough data for XGBoost."}

        model = XGBRegressor(n_estimators=100)
        model.fit(X, y)

        last_window = list(data[-lag:])
        preds = []

        for _ in range(steps):
            pred = model.predict(np.array(last_window[-lag:]).reshape(1, -1))[0]
            preds.append(pred)
            last_window.append(pred)

        return [{"forecast": float(p), "lower_conf_int": None, "upper_conf_int": None} for p in preds]

    except Exception as e:
        logging.error(f"XGBoost error: {e}")
        return {"error": "XGBoost failed"}


# ---------------------- RANDOM FOREST ----------------------
def random_forest_forecast(df, dependent_col, steps=10, lag=10):
    try:
        print("\n🚀 Running Random Forest Forecast")
        data = df[dependent_col].values
        X, y = [], []

        for i in range(lag, len(data)):
            X.append(data[i-lag:i])
            y.append(data[i])

        if len(X) == 0:
            return {"error": "Not enough data for RandomForest."}

        model = RandomForestRegressor(n_estimators=100)
        model.fit(X, y)

        last_window = list(data[-lag:])
        preds = []

        for _ in range(steps):
            pred = model.predict(np.array(last_window[-lag:]).reshape(1, -1))[0]
            preds.append(pred)
            last_window.append(pred)

        return [{"forecast": float(p), "lower_conf_int": None, "upper_conf_int": None} for p in preds]

    except Exception as e:
        logging.error(f"RandomForest error: {e}")
        return {"error": "RandomForest failed"}


# ---------------------- GENERATE FORECASTS ----------------------
def generate_forecasts(dataset_name, dependent_col, steps=10):
    """Fetch data and generate forecasts using all models."""
    df = fetch_data(dataset_name, dependent_col)

    if df.empty:
        return {"error": "No valid data available."}

    print(f"\n✅ Dataset '{dataset_name}' - Column '{dependent_col}': {df.shape[0]} rows")

    forecasts = {
        "ARIMA": arima_forecast(df, dependent_col, steps),
        "SARIMA": sarima_forecast(df, dependent_col, steps),
        "XGBoost": xgboost_forecast(df, dependent_col, steps),
        "RandomForest": random_forest_forecast(df, dependent_col, steps)
    }
    print(forecasts)
    return forecasts
