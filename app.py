from flask import Flask, render_template, request, jsonify
from fetch import fetch_data as fetch_api_data
import sqlite3
import json
from eda import generate_plots
from models import generate_forecasts   # Updated models.py expected
from evaluators import evaluate_models
import os

# Disable TensorFlow OneDNN logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

app = Flask(__name__)

# Ensure necessary folders exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# -------- Page Routes --------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/app")
def app_dashboard():
    dataset_name = request.args.get('dataset_name')
    return render_template("app.html", dataset_name=dataset_name)

@app.route("/eda_page")
def eda_page():
    dataset_name = request.args.get('dataset_name')
    return render_template("eda.html", dataset_name=dataset_name)

@app.route("/forecast_page")
def forecast_page():
    dataset_name = request.args.get('dataset_name')
    print("Received dataset_name:", dataset_name)  # Debugging log
    return render_template("forecast.html", dataset_name=dataset_name)


@app.route("/evaluate_page")
def evaluate_page():
    dataset_name = request.args.get('dataset_name')
    return render_template("evaluate.html", dataset_name=dataset_name)

@app.route("/view_table")
def view_table_page():
    dataset_name = request.args.get('dataset_name')
    return render_template("table.html", dataset_name=dataset_name)

# -------- API Routes --------
@app.route("/api/get_dataset")
def api_get_dataset():
    dataset_name = request.args.get('dataset_name')

    if not dataset_name:
        return jsonify({"error": "Dataset name is missing."}), 400

    conn = sqlite3.connect("data_storage.db")
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp, data FROM timeseries_data WHERE dataset_name = ?", (dataset_name,))
    rows = cursor.fetchall()

    cursor.execute("SELECT keys FROM timeseries_data WHERE dataset_name = ? LIMIT 1", (dataset_name,))
    keys_row = cursor.fetchone()
    conn.close()

    if not rows or not keys_row:
        return jsonify({"keys": [], "rows": []})

    keys = json.loads(keys_row[0])
    if "timestamp" not in keys:
        keys.insert(0, "timestamp")

    table_rows = []
    for timestamp, data_json in rows:
        row_data = json.loads(data_json)
        row_data["timestamp"] = timestamp
        table_rows.append(row_data)

    return jsonify({"keys": keys, "rows": table_rows})

@app.route("/fetch", methods=["POST"])
def fetch_data_endpoint():
    data = request.form
    api_url = data.get("api_url")
    dataset_name = data.get("dataset_name")

    if not api_url or not dataset_name:
        return jsonify({"error": "API URL and Dataset Name are required."}), 400

    result = fetch_api_data(api_url, dataset_name)
    return jsonify(result)

@app.route("/eda", methods=["POST"])
def eda():
    data = request.form
    dataset_name = data.get("dataset_name")
    dependent_col = data.get("dependent_col", "close_price")
    moving_avg_window = int(data.get("moving_avg_window", 7))
    heatmap_window = data.get("heatmap_window", "weekly_vs_hours")

    if not dataset_name:
        return jsonify({"error": "Dataset Name is required."}), 400

    result = generate_plots(dataset_name, dependent_col, moving_avg_window, heatmap_window)
    return jsonify(result)

# -------- Updated Forecast Endpoint --------
@app.route("/forecast", methods=["POST"])
def forecast():
    data = request.form
    dataset_name = data.get("dataset_name")
    dependent_col = data.get("dependent_col")
    steps = data.get("steps")

    if not dataset_name or not dependent_col or not steps:
        return jsonify({"error": "Dataset Name, Dependent Column, and Steps are required."}), 400

    try:
        steps = int(steps)
        forecast_result = generate_forecasts(dataset_name, dependent_col, steps)
        print(forecast_result)
        return jsonify(forecast_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.form
    dataset_name = data.get("dataset_name")
    dependent_col = data.get("dependent_col")

    if not dataset_name or not dependent_col:
        return jsonify({"error": "Dataset Name and Dependent Column are required."}), 400

    result = evaluate_models(dataset_name, dependent_col)
    return jsonify(result)

@app.route("/list_datasets")
def list_datasets():
    from fetch import list_datasets_from_db
    datasets = list_datasets_from_db()
    return jsonify({"datasets": datasets})

# -------- App Runner --------
if __name__ == "__main__":

    app.run(host="0.0.0.0", debug=False)
