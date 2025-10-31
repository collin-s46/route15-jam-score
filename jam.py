import os
import json
import requests
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pytz

# --------------------------
# Load service account and config from local JSON
# --------------------------
local_file = "route15-logger.json"

try:
    with open(local_file) as f:
        key_dict = json.load(f)
    print(f"✅ Loaded SERVICE_ACCOUNT_JSON from local file: {local_file}")
except FileNotFoundError:
    raise RuntimeError(f"❌ No SERVICE_ACCOUNT_JSON found. Please create {local_file}")

# If your JSON contains DEPARTURE_TIME, read it
departure_time_str = key_dict.get("DEPARTURE_TIME", "08:30")  # default 08:30 if not set
print(f"✅ Using departure time: {departure_time_str}")

# Google Maps API key (optional: put in your JSON or set as env variable)
API_KEY = key_dict.get("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GOOGLE_MAPS_API_KEY not set in JSON or environment variable.")

# --------------------------
# Google Sheets setup
# --------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(key_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open("Route 15 Jam Log").worksheet("Log")

# --------------------------
# Define trip info
# --------------------------
origin = "15783 Dorneywood Dr, Leesburg, VA 20176"
destination = "801 N King St, Leesburg, VA 20176"
eastern = pytz.timezone("US/Eastern")

# Build departure datetime
today = datetime.now(eastern).date()
try:
    departure_dt_naive = datetime.strptime(f"{today} {departure_time_str}", "%Y-%m-%d %H:%M")
except ValueError:
    raise ValueError(f"DEPARTURE_TIME format invalid: '{departure_time_str}'. Use HH:MM (e.g., 08:30)")

departure_dt = eastern.localize(departure_dt_naive)
departure_unix = int(departure_dt.timestamp())

# --------------------------
# Call Google Maps API
# --------------------------
url = "https://maps.googleapis.com/maps/api/distancematrix/json"
params = {
    "origins": origin,
    "destinations": destination,
    "departure_time": departure_unix,
    "key": API_KEY,
}
response = requests.get(url, params=params)
data = response.json()
print("Full API response:", data)

# --------------------------
# Calculate jam score and log to Sheets
# --------------------------
try:
    travel_time_sec = data["rows"][0]["elements"][0]["duration_in_traffic"]["value"]
    travel_time_min = travel_time_sec / 60
    baseline_time = 9  # in minutes
    jam_score = (baseline_time / travel_time_min) * 100
    jam_score = min(jam_score, 100)

    # Combine date with departure time
    full_departure_datetime = departure_dt

    # Append row to Google Sheet: Date | Day | Departure Time | Jam Score | Travel Time
    sheet.append_row([
        full_departure_datetime.strftime("%Y-%m-%d"),
        full_departure_datetime.strftime("%A"),
        full_departure_datetime.strftime("%H:%M"),
        round(jam_score, 1),
        round(travel_time_min, 2)
    ])
    print(f"✅ Logged to Google Sheets for {departure_time_str}")

except Exception as e:
    print(f"API error for {departure_time_str}:", e)
