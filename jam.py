import os
import json
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pytz

# --------------------------
# Load SERVICE_ACCOUNT_JSON
# --------------------------
service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")

if service_account_json:
    key_dict = json.loads(service_account_json)
    print("✅ Loaded SERVICE_ACCOUNT_JSON from environment variable.")
else:
    # Only fallback to local JSON if it exists (for local testing)
    local_file = "route15-logger.json"
    if os.path.exists(local_file):
        with open(local_file) as f:
            key_dict = json.load(f)
        print(f"✅ Loaded SERVICE_ACCOUNT_JSON from local file: {local_file}")
    else:
        raise RuntimeError(
            "❌ SERVICE_ACCOUNT_JSON not found. "
            "Set it as an environment variable (Render) or create route15-logger.json for local testing."
        )

# --------------------------
# Load DEPARTURE_TIME
# --------------------------
departure_time_str = os.environ.get("DEPARTURE_TIME") or key_dict.get("DEPARTURE_TIME")
if not departure_time_str:
    departure_time_str = "08:30"  # fallback default for local testing
print(f"✅ Using departure time: {departure_time_str}")

# --------------------------
# Load GOOGLE_MAPS_API_KEY
# --------------------------
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY") or key_dict.get("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GOOGLE_MAPS_API_KEY not set in env variables or JSON.")

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
# Trip info
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
