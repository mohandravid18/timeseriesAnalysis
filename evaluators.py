import pandas as pd
import numpy as np
import sqlite3
import json
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Flask

from sklearn.metrics import mean_absolute_error, mean_squared_error
from models import generate_forecasts  # Import forecast function

# Configure logging
logging.basicConfig(filename="evaluators.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DATABASE_NAME = "data_storage.db"
FORECAST_STEPS = 10  # Number of steps to predict


def fetch_actual_values(dataset_name, dependent_col):

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        query = """
            SELECT DISTINCT timestamp, data FROM timeseries_data 
            WHERE dataset_name = ? 
            ORDER BY timestamp DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(dataset_name, FORECAST_STEPS * 2))  # Fetch extra in case of duplicates
        conn.close()

        if df.empty:
            logging.warning(f"WARNING: No data found for dataset '{dataset_name}'.")
            return []

        df["data"] = df["data"].apply(json.loads)
        data_expanded = pd.json_normalize(df["data"])
        df = df.drop(columns=["data"]).join(data_expanded)

        # Debugging: Print actual column names
        print("DEBUG: DataFrame Columns in Evaluator:", df.columns.tolist())

        if dependent_col not in df.columns:
            logging.error(f"ERROR: Column '{dependent_col}' not found in dataset.")
            return []

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")  # Ensure chronological order

        # Get the last unique values for comparison
        unique_actual_values = df.drop_duplicates(subset=["timestamp"]).tail(FORECAST_STEPS)

        # Convert to numeric and handle any errors
        unique_actual_values[dependent_col] = pd.to_numeric(unique_actual_values[dependent_col], errors="coerce")
        unique_actual_values.dropna(subset=[dependent_col], inplace=True)

        actual_values = unique_actual_values[dependent_col].tolist()
        logging.info(f"Fetched actual values: {actual_values}")

        return actual_values

    except Exception as e:
        logging.error(f"ERROR: Database error in Evaluator: {e}")
        return []


def calculate_metrics(actual, forecast):

    if len(actual) != len(forecast):
        logging.error("ERROR: Mismatch in actual and forecasted data length.")
        return {"error": "Mismatch in actual and forecasted data length."}

    mae = mean_absolute_error(actual, forecast)

    # Handling potential TypeError for `squared` argument
    try:
        rmse = mean_squared_error(actual, forecast, squared=False)
    except TypeError:
        rmse = np.sqrt(mean_squared_error(actual, forecast))  # Manual RMSE calculation

    # Prevent division by zero in MAPE calculation
    actual_array = np.array(actual)
    forecast_array = np.array(forecast)

    # Avoid NaN issues in MAPE
    mape = np.mean(np.abs((actual_array - forecast_array) / np.where(actual_array == 0, np.nan, actual_array))) * 100
    mape = np.nan_to_num(mape)  # Replace NaN with zero if encountered

    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def convert_numpy_to_python(obj):

    if isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.float32, np.float64, np.int32, np.int64)):
        return float(obj)  # Convert to standard Python float
    else:
        return obj


def evaluate_models(dataset_name, dependent_col):
    try:
        print(f"Evaluating models for dataset: {dataset_name}, column: {dependent_col}")
        actual_values = fetch_actual_values(dataset_name, dependent_col)

        if len(actual_values) < FORECAST_STEPS:
            error_msg = f"ERROR: Insufficient actual data for {FORECAST_STEPS}-step evaluation."
            logging.error(error_msg)
            return {"error": error_msg}

        forecasts = generate_forecasts(dataset_name, dependent_col, steps=FORECAST_STEPS)

        if not forecasts:
            return {"error": "No forecasts generated."}

        results = {}
        for model, forecast in forecasts.items():
            if isinstance(forecast, list):  # Ensure it's a list of dictionaries
                forecast_values = [entry["forecast"] for entry in forecast if isinstance(entry, dict) and "forecast" in entry]
            else:
                forecast_values = []

            if len(forecast_values) < FORECAST_STEPS:
                logging.error(f"Model '{model}' failed to generate a valid forecast.")
                results[model] = {"error": "Forecast generation failed"}
                continue

            print(f"DEBUG: Actual ({len(actual_values)}) vs Forecast ({len(forecast_values)}) for {model}")
            metrics = calculate_metrics(actual_values, forecast_values)
            results[model] = metrics
            logging.info(f"Evaluation for {model}: {metrics}")

        ranked_models = sorted(results.items(),
                               key=lambda x: (x[1].get("MAE", float("inf")), x[1].get("RMSE", float("inf"))))

        return convert_numpy_to_python({"ranked_models": ranked_models, "metrics": results})

    except Exception as e:
        logging.error(f"INTERNAL SERVER ERROR: {e}", exc_info=True)
        return {"error": "Internal server error."}
