import csv
import math
import requests
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"
SLEEP_TIME = 1.0  

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def road_distance_km(lat1, lon1, lat2, lon2):
    url = f"{OSRM_URL}{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}
    r = requests.get(url, params=params)
    data = r.json()
    if data.get("code") != "Ok":
        return None
    return data["routes"][0]["distance"] / 1000.0  

teams = []
stadium = {}
facility = {}
airport = {}

with open(PROJECT_ROOT / "data" / "intermediate" / "coordinates.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        team = row["team"]
        teams.append(team)
        stadium[team] = (float(row["stadium_lat"]), float(row["stadium_lon"]))
        facility[team] = (float(row["facility_lat"]), float(row["facility_lon"]))
        airport[team] = (float(row["airport_lat"]), float(row["airport_lon"]))

with open(PROJECT_ROOT / "data" / "distances" / "HomeFacility_HomeStadium.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["team", "distance_km"])
    for team in teams:
        d = road_distance_km(*facility[team], *stadium[team])
        writer.writerow([team, d])
        time.sleep(SLEEP_TIME)

with open(PROJECT_ROOT / "data" / "distances" / "HomeFacility_HomeAirport.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["team", "distance_km"])
    for team in teams:
        d = road_distance_km(*facility[team], *airport[team])
        writer.writerow([team, d])
        time.sleep(SLEEP_TIME)

with open(PROJECT_ROOT / "data" / "distances" / "HomeStadium_HomeAirport.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["team", "distance_km"])
    for team in teams:
        d = road_distance_km(*stadium[team], *airport[team])
        writer.writerow([team, d])
        time.sleep(SLEEP_TIME)

with open(PROJECT_ROOT / "data" / "distances" / "HomeFacility_AwayStadium.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["away_team", "home_team", "distance_km"])
    for away in teams:
        for home in teams:
            d = road_distance_km(*facility[away], *stadium[home])
            writer.writerow([away, home, d])
            time.sleep(SLEEP_TIME)

with open(PROJECT_ROOT / "data" / "distances" / "HomeAirport_AwayAirport.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["team_i", "team_j", "distance_km"])
    for i in teams:
        for j in teams:
            d = haversine_km(*airport[i], *airport[j])
            writer.writerow([i, j, d])
