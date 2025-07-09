import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime

# Load environment variables from the .env file in the current directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Define start and end addresses
origin = "15783 Dorneywood Dr, Leesburg, VA 20176"
destination = "801 N King St, Leesburg, VA 20176"

# Build the request URL
url = "https://maps.googleapis.com/maps/api/distancematrix/json"
params = {
    "origins": origin,
    "destinations": destination,
    "departure_time": "now",
    "key": API_KEY,
}

# Make the request
response = requests.get(url, params=params)
data = response.json()

# Get travel time in seconds
travel_time_sec = data["rows"][0]["elements"][0]["duration_in_traffic"]["value"]

# Convert to minutes
travel_time_min = travel_time_sec / 60

# Define your baseline travel time (perfect, no-traffic trip)
baseline_time = 9  # in minutes

# Calculate Jam Score
jam_score = (baseline_time / travel_time_min) * 100

# Cap at 100%
jam_score = min(jam_score, 100)


#csv file appendation

# Today's date
today = datetime.now().strftime("%Y-%m-%d")

# Build row of data
row = {
    "date": today,
    "travel_time_min": round(travel_time_min, 1),
    "jam_score": round(jam_score, 1),
}

# CSV path
csv_path = os.path.join(os.path.dirname(__file__), "jam.csv")

# Check if file exists
try:
    df = pd.read_csv(csv_path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
except FileNotFoundError:
    df = pd.DataFrame([row])

# Save it back
df.to_csv(csv_path, index=False)

print("Logged to CSV.")
print(f"Script ran at {datetime.now()}")


print(f"Jam Score: {jam_score:.1f}%")


print(f"Travel time: {travel_time_min:.2f} minutes")
