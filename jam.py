import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import pytz

# Load environment variables from the .env file in the current directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Define start and end addresses
origin = "15783 Dorneywood Dr, Leesburg, VA 20176"
destination = "801 N King St, Leesburg, VA 20176"

# Read service account JSON from environment
key_dict = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])

# Set up credentials and Sheets client
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(key_dict, scopes=scope)
client = gspread.authorize(creds)

# Open your sheet and tab
sheet = client.open("Route 15 Jam Log").worksheet("Log")

# Prepare for loop
eastern = pytz.timezone("US/Eastern")

# Step 1: Get departure time from env variable (required)
departure_time_str = os.getenv("DEPARTURE_TIME", None)
if not departure_time_str:
    raise ValueError("DEPARTURE_TIME environment variable not set.")

# Use today's date in US/Eastern timezone
now = datetime.now(eastern)
today = now.date()

# Build departure datetime in US/Eastern
try:
    departure_dt_naive = datetime.strptime(f"{today} {departure_time_str}", "%Y-%m-%d %H:%M")
except ValueError:
    raise ValueError(f"DEPARTURE_TIME format invalid: '{departure_time_str}'. Use HH:MM (e.g., 08:30)")

departure_dt = eastern.localize(departure_dt_naive)
departure_unix = int(departure_dt.timestamp())

url = "https://maps.googleapis.com/maps/api/distancematrix/json"

# Build the request URL for this departure time
params = {
    "origins": origin,
    "destinations": destination,
    "departure_time": departure_unix,
    "key": API_KEY,
}
response = requests.get(url, params=params)
data = response.json()

try:
    travel_time_sec = data["rows"][0]["elements"][0]["duration_in_traffic"]["value"]
    travel_time_min = travel_time_sec / 60
    baseline_time = 9  # in minutes
    jam_score = (baseline_time / travel_time_min) * 100
    jam_score = min(jam_score, 100)

    # Log to Google Sheets (columns: Date | Day | Departure Time | Jam Score | Travel Time)
    sheet.append_row([
        departure_time.date().isoformat(),
        departure_time.strftime("%A"),
        departure_time.strftime("%H:%M"),
        round(jam_score, 1),
        round(travel_time_min, 2)
    ])
    print(f"✅ Logged to Google Sheets for {departure_time}")

except Exception as e:
    print(f"API error for {departure_time}:", e)


