from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import io
import urllib.parse as urlp
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)

def get_time_series(start_date, end_date, latitude, longitude, variable):
    """
    Calls NASA Data Rods service to get a time series for a specific variable.
    """
    base_url = "https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"
    query_parameters = {
        "variable": variable,
        "type": "asc2",
        "location": f"GEOM:POINT({longitude}, {latitude})",
        "startDate": start_date,
        "endDate": end_date,
    }
    full_url = base_url + "?" + "&".join(
        [f"{key}={urlp.quote(str(val))}" for key, val in query_parameters.items()]
    )

    r = requests.get(full_url)
    if r.status_code != 200:
        raise Exception(f"Error {r.status_code}: {r.text}")
    return r.text

def parse_time_series(ts_str):
    """
    Parses the ASCII time series response from Data Rods into a DataFrame.
    """
    df = pd.read_table(
        io.StringIO(ts_str),
        sep="\t",
        names=["time", "data"],
        header=10,
        parse_dates=["time"]
    )
    return df

@app.route("/api/weather", methods=["POST"])
def weather_data():
    """
    POST endpoint: user provides start_date, end_date, latitude, longitude
    - NASA data is always fetched for 2015-2020
    - Then filtered to the user's start & end dates
    - Calculates monthly averages and 6-month predictions
    """
    data = request.get_json()
    user_start_date = data.get("start_date")
    user_end_date = data.get("end_date")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    # Validate input
    if not all([user_start_date, user_end_date, latitude, longitude]):
        return jsonify({"error": "Missing one or more required parameters"}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return jsonify({"error": "Latitude and longitude must be numbers"}), 400

    # Fixed NASA data range
    nasa_start = "2015-01-01T00"
    nasa_end = "2020-12-31T00"

    try:
        # Fetch precipitation data for the fixed range
        df_precip = parse_time_series(get_time_series(
            nasa_start, nasa_end, latitude, longitude,
            variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Rainf"
        ))

        # Aggregate daily totals
        df_precip = df_precip.groupby(pd.Grouper(key='time', freq='1D')).sum().reset_index()

        # Convert user dates
        u_start = datetime.strptime(user_start_date, "%Y-%m-%dT%H")
        u_end = datetime.strptime(user_end_date, "%Y-%m-%dT%H")

        # Filter to user's range (must fall within 2015–2020)
        df_filtered = df_precip[(df_precip["time"] >= u_start) & (df_precip["time"] <= u_end)]

        if df_filtered.empty:
            return jsonify({"error": "No data available in the selected range (must be within 2015–2020)"}), 404

        # Compute monthly averages in user's range
        df_filtered["month"] = df_filtered["time"].dt.month
        monthly_avg = df_filtered.groupby("month")["data"].mean().reset_index()

        # Compute average daily precipitation
        avg_precip = df_filtered["data"].mean()

        # Predict 6 months after user_end_date
        predictions = []
        for i in range(1, 7):
            next_month = ((u_end.month + i - 1) % 12) + 1
            avg_for_month = monthly_avg.loc[monthly_avg["month"] == next_month, "data"]
            predicted_val = float(avg_for_month.values[0]) if not avg_for_month.empty else 0
            predictions.append({
                "month": next_month,
                "predicted_avg_precip_mm": round(predicted_val, 2)
            })

        response = {
            "metadata": {
                "latitude": latitude,
                "longitude": longitude,
                "nasa_data_range_used": f"{nasa_start} to {nasa_end}",
                "user_data_range": f"{user_start_date} to {user_end_date}",
                "average_daily_precip_mm": round(avg_precip, 2)
            },
            "filtered_daily_precip": df_filtered[["time", "data"]].to_dict(orient="records"),
            "monthly_averages": monthly_avg.to_dict(orient="records"),
            "six_month_predictions": predictions
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "NASA Weather API is running."})

if __name__ == "__main__":
    app.run(debug=True)
