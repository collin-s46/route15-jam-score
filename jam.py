import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import pytz
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# 1. Load Google service account JSON
service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
if service_account_json:
    key_dict = json.loads(service_account_json)
    print("✅ Loaded SERVICE_ACCOUNT_JSON from environment variable.")
else:
    local_file = "route15-logger.json"
    try:
        with open(local_file) as f:
            key_dict = json.load(f)
        print(f"✅ Loaded SERVICE_ACCOUNT_JSON from local file: {local_file}")
    except FileNotFoundError:
        raise RuntimeError(f"❌ No SERVICE_ACCOUNT_JSON found. Please set env var or create {local_file}")

# 2. API Key and Sheet setup
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(key_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("Route 15 Jam Log").worksheet("Log")

# 3. Route info
origin = "15783 Dorneywood Dr, Leesburg, VA 20176"
destination = "801 N King St, Leesburg, VA 20176"

# 4. Departure time
departure_time_str = os.getenv("DEPARTURE_TIME", None)
if not departure_time_str:
    raise ValueError("DEPARTURE_TIME environment variable not set.")
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
today = now.date()

try:
    departure_dt_naive = datetime.strptime(f"{today} {departure_time_str}", "%Y-%m-%d %H:%M")
except ValueError:
    raise ValueError(f"DEPARTURE_TIME format invalid: '{departure_time_str}'. Use HH:MM (e.g., 08:30)")

departure_dt = eastern.localize(departure_dt_naive)
departure_unix = int(departure_dt.timestamp())

# 5. Call Google Maps API
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

try:
    travel_time_sec = data["rows"][0]["elements"][0]["duration_in_traffic"]["value"]
    travel_time_min = travel_time_sec / 60
    baseline_time = 9  # in minutes
    jam_score = (baseline_time / travel_time_min) * 100
    jam_score = min(jam_score, 100)

    # Log to Google Sheets
    sheet.append_row([
        now.strftime("%Y-%m-%d"),
        now.strftime("%A"),
        departure_time_str,
        round(jam_score, 1),
        round(travel_time_min, 2)
    ])
    print(f"✅ Logged {departure_time_str} successfully")

    # 6. Send email notification (only at 8:40)
    if departure_time_str == "08:40":
        records = sheet.get_all_records()
        last_two = records[-2:]  # Get last 2 rows

        msg_body = "Route 15 Traffic Update:\n\n"
        for row in last_two:
            msg_body += f"{row['Departure']} -- Travel Time: {row['Travel Time']} - Jam Score: {row['Jam Score']}\n"

        sender = os.getenv("GMAIL_ADDRESS")
        password = os.getenv("GMAIL_APP_PASSWORD")
        recipient = sender

        msg = MIMEText(msg_body)
        msg["Subject"] = f"Route 15 Jam Scores ({now.strftime('%A')})"
        msg["From"] = sender
        msg["To"] = recipient

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("📧 Email sent with latest jam scores.")

except Exception as e:
    print(f"API or Sheet error for {departure_time_str}:", e)
