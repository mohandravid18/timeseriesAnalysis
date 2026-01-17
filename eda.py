import pandas as pd
import sqlite3
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Flask

import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import logging
import os

# Configure logging
logging.basicConfig(
    filename="eda.log", level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DATABASE_NAME = "data_storage.db"
PLOT_DIR = "static/plots"

# Ensure plot directory exists
os.makedirs(PLOT_DIR, exist_ok=True)

def fetch_data_from_db(dataset_name):

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Check if dataset exists
        cursor.execute("SELECT COUNT(*) FROM timeseries_data WHERE dataset_name = ?", (dataset_name,))
        if cursor.fetchone()[0] == 0:
            logging.warning(f"Dataset '{dataset_name}' not found in database.")
            return pd.DataFrame()

        query = "SELECT timestamp, data FROM timeseries_data WHERE dataset_name = ?"
        df = pd.read_sql_query(query, conn, params=(dataset_name,))
        conn.close()

        if df.empty:
            logging.warning(f"No data found for dataset '{dataset_name}'.")
            return df

        # Convert JSON data to DataFrame
        df["data"] = df["data"].apply(json.loads)
        data_expanded = pd.json_normalize(df["data"])
        df = df.drop(columns=["data"]).join(data_expanded)

        # Debugging: Print column names
        print("DEBUG: DataFrame Columns:", df.columns.tolist())

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        if df["timestamp"].isna().any():
            logging.error(f"Invalid timestamps detected in dataset '{dataset_name}'.")
            df = df.dropna(subset=["timestamp"])

        return df

    except Exception as e:
        logging.error(f"Database error: {e}")
        return pd.DataFrame()

def preprocess_data(df, dependent_col):

    if dependent_col not in df.columns:
        logging.error(f"Column '{dependent_col}' not found in dataset.")
        raise ValueError(f"Column '{dependent_col}' not found in dataset.")

    # Convert the dependent column to numeric (force conversion)
    df[dependent_col] = pd.to_numeric(df[dependent_col], errors="coerce")

    if df[dependent_col].isna().all():
        logging.error(f"Column '{dependent_col}' could not be converted to numeric.")
        raise ValueError(f"Column '{dependent_col}' is not numeric.")

    df = df.sort_values(by="timestamp")
    df = df.dropna(subset=[dependent_col])  # Drop NaN values in dependent column

    return df

def save_plot(fig):

    import uuid
    plot_filename = f"{PLOT_DIR}/{uuid.uuid4().hex}.png"
    fig.savefig(plot_filename, bbox_inches="tight")
    plt.close(fig)
    return plot_filename

def adf_test(series):

    try:
        result = adfuller(series.dropna())
        p_value = result[1]
        stationarity = "Stationary" if p_value < 0.05 else "Non-Stationary"
        return p_value, stationarity
    except Exception as e:
        logging.error(f"ADF Test Error: {e}")
        return None, "Error in ADF Test"

def generate_plots(dataset_name, dependent_col, moving_avg_window=7, heatmap_window=24):

    df = fetch_data_from_db(dataset_name)
    if df.empty:
        return {"error": "No data available in the database."}

    try:
        df = preprocess_data(df, dependent_col)
    except ValueError as e:
        return {"error": str(e)}

    plots = {}

    # Time-Series Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["timestamp"], df[dependent_col], label="Time Series", color="blue")
    ax.set_title(f"{dependent_col} Over Time")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel(dependent_col)
    ax.legend()
    ax.grid()
    plots["time_series"] = save_plot(fig)

    # Trend, Seasonality, and Cyclic Components
    if len(df) >= 30:  # Ensure enough data points
        try:
            decomposition = seasonal_decompose(df[dependent_col], period=min(len(df) // 2, 30), model="additive")

            fig, axes = plt.subplots(3, 1, figsize=(10, 10))
            axes[0].plot(decomposition.trend, label="Trend", color="green")
            axes[0].set_title("Trend Component")
            axes[1].plot(decomposition.seasonal, label="Seasonality", color="purple")
            axes[1].set_title("Seasonality Component")
            axes[2].plot(decomposition.resid, label="Cyclic Component", color="orange")
            axes[2].set_title("Cyclic Component")
            for ax in axes:
                ax.legend()
            plots["trend_seasonality"] = save_plot(fig)
        except Exception as e:
            logging.warning(f"Seasonal decomposition failed: {e}")

    else:
        logging.warning(f"Not enough data points ({len(df)}) for seasonal decomposition.")

    # Moving Average Plot
    df["Moving_Avg"] = df[dependent_col].rolling(window=moving_avg_window, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["timestamp"], df[dependent_col], label=dependent_col, color="blue", linestyle="dashed")
    ax.plot(df["timestamp"], df["Moving_Avg"], label=f"Moving Avg ({moving_avg_window} Points)", linestyle="solid", color="red")
    ax.set_title("Moving Average Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel(dependent_col)
    ax.legend()
    ax.grid()
    plots["moving_avg"] = save_plot(fig)
    # Heatmap Plot
    try:
        # Create necessary date parts
        df["Day_of_Week"] = df["timestamp"].dt.day_name()
        df["Hour"] = df["timestamp"].dt.hour
        df["Week"] = df["timestamp"].dt.isocalendar().week
        df["Month"] = df["timestamp"].dt.month_name()

        # Dynamic pivot table based on user selection
        if heatmap_window == "weekly_vs_hours":
            pivot_table = df.pivot_table(values=dependent_col, index="Day_of_Week", columns="Hour", aggfunc="mean")
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot_table = pivot_table.reindex(day_order)  # Reorder days
        elif heatmap_window == "weeks_vs_months":
            pivot_table = df.pivot_table(values=dependent_col, index="Week", columns="Month", aggfunc="mean")
        elif heatmap_window == "hours_vs_months":
            pivot_table = df.pivot_table(values=dependent_col, index="Hour", columns="Month", aggfunc="mean")
        else:
            pivot_table = df.pivot_table(values=dependent_col, index="Hour", columns="Day_of_Week", aggfunc="mean")

        # Fill missing data
        pivot_table.fillna(0, inplace=True)

        # Plot heatmap
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.heatmap(pivot_table, cmap="coolwarm", linewidths=0.5, annot=True, fmt=".1f", ax=ax)
        ax.set_title(f"Heatmap of {dependent_col}")
        plots["heatmap"] = save_plot(fig)
    except Exception as e:
        logging.warning(f"Heatmap generation failed: {e}")

    # ADF Test
    adf_p_value, stationarity = adf_test(df[dependent_col])
    plots["adf_test"] = {"p_value": adf_p_value, "stationarity": stationarity}

    return plots
