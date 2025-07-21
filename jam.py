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
departure_times = ["20:59", "21:00", "21:01", "21:02"]
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
today_date = now.strftime("%Y-%m-%d")
today_day = now.strftime("%A")

url = "https://maps.googleapis.com/maps/api/distancematrix/json"

for time_str in departure_times:
    hour, minute = map(int, time_str.split(":"))
    departure_dt = eastern.localize(datetime(now.year, now.month, now.day, hour, minute))
    departure_unix = int(departure_dt.timestamp())

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
            today_date,
            today_day,
            time_str,
            round(jam_score, 1),
            round(travel_time_min, 2)
        ])
        print(f"✅ Logged to Google Sheets for {time_str}")

    except Exception as e:
        print(f"API error for {time_str}:", e)


