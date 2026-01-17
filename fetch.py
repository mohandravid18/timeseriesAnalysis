import requests
import pandas as pd
import sqlite3
import json

DATABASE_NAME = "data_storage.db"


def fetch_data(api_url, dataset_name="default"):

    try:
        # Fetch data from API
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # Dynamically identify time-series key (e.g., "Time Series (5min)")
        time_series_key = next((key for key in data.keys() if "Time Series" in key), None)
        if not time_series_key:
            raise ValueError("No valid time-series data found in API response.")

        # Convert nested time-series data into DataFrame
        df = pd.DataFrame.from_dict(data[time_series_key], orient="index")
        df.reset_index(inplace=True)

        # Detect and format timestamp column
        df, timestamp_col = detect_timestamp_column(df)
        if not timestamp_col:
            raise ValueError("No valid timestamp column detected in the data.")

        # Ensure time-series is sorted chronologically
        df = df.sort_values(by="timestamp")

        # Store processed data in SQLite
        keys = df.columns.tolist()
        store_data(dataset_name, df, keys)

        return {"status": "success", "keys": keys}

    except Exception as e:
        print(" Fetch Data Error:", str(e))
        return {"status": "error", "message": str(e)}



def detect_timestamp_column(df):

    df.columns = [col.lower().strip() for col in df.columns]  # Standardize column names
    timestamp_col = None

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            timestamp_col = col
            break
        elif pd.api.types.is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')  # Try parsing as datetime
                if df[col].notna().all():  # If successful for all rows
                    timestamp_col = col
                    break
            except Exception:
                continue

    if timestamp_col:
        df[timestamp_col] = df[timestamp_col].dt.strftime("%Y-%m-%d %H:%M:%S")  # Standard timestamp format

        # Rename to "timestamp" for consistency
        if timestamp_col != "timestamp":
            df.rename(columns={timestamp_col: "timestamp"}, inplace=True)
            timestamp_col = "timestamp"

    return df, timestamp_col



def store_data(dataset_name, df, keys):

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create main timeseries table (if doesn't exist)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeseries_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_name TEXT,
            timestamp TEXT,
            data TEXT,
            keys TEXT
        )
    """)

    # Insert each row of the dataset
    for _, row in df.iterrows():
        timestamp = row.get("timestamp")
        if not timestamp:
            continue

        # Store row data as JSON, excluding timestamp
        data = json.dumps(row.drop("timestamp").to_dict())
        cursor.execute("""
            INSERT INTO timeseries_data (dataset_name, timestamp, data, keys)
            VALUES (?, ?, ?, ?)
        """, (dataset_name, timestamp, data, json.dumps(keys)))  # Store keys as JSON for metadata

    conn.commit()
    conn.close()
    print(f" Data stored successfully under dataset '{dataset_name}'.")




def list_datasets_from_db():
    """List all unique dataset names stored in the database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Fetch distinct dataset names
        cursor.execute("SELECT DISTINCT dataset_name FROM timeseries_data")
        datasets = [row[0] for row in cursor.fetchall()]
        conn.close()

        print(" Available datasets:", datasets)
        return datasets

    except Exception as e:
        print(" ERROR fetching datasets:", str(e))
        return []
