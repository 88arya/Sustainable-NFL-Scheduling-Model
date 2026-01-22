import requests
import time
import csv
from pathlib import Path

from ..matchups.rankings import teams_order

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

stadiums_order = [
    "Highmark Stadium",
    "Hard Rock Stadium",
    "Gillette Stadium",
    "MetLife Stadium",
    "M&T Bank Stadium",
    "Paycor Stadium",
    "Huntington Bank Field",
    "Acrisure Stadium",
    "NRG Stadium",
    "Lucas Oil Stadium",
    "EverBank Stadium",
    "Nissan Stadium, Nashville",
    "Empower Field at Mile High",
    "Arrowhead Stadium",
    "Allegiant Stadium",
    "SoFi Stadium",
    "AT&T Stadium",
    "MetLife Stadium",
    "Lincoln Financial Field",
    "Northwest Stadium",
    "Soldier Field",
    "Ford Field",
    "Lambeau Field",
    "U.S. Bank Stadium",
    "Mercedes-Benz Stadium",
    "Bank of America Stadium",
    "Caesars Superdome",
    "Raymond James Stadium",
    "State Farm Stadium",
    "SoFi Stadium",
    "Levi's Stadium",
    "Lumen Field"
]

facilities_order = [
    "ADPRO Sports Training Center",
    "Hard Rock Stadium",
    "Gillette Stadium",
    "Atlantic Health Jets Training Center",
    "1 Winning Dr, Owings Mills",
    "IEL Indoor Facility",
    "76 Lou Groza Blvd, Berea",
    "3200 S Water St, Pittsburgh",
    "Houston Methodist Training Center",
    "7001 W 56th St, Indianapolis",
    "EverBank Stadium",
    "Saint Thomas Sports Park",
    "Denver Broncos NFL Football Headquarters Campus",
    "Missouri Western State University",
    "Intermountain Health Performance Center",
    "The Bolt - Home of the Los Angeles Chargers",
    "Dallas Cowboys Headquarters",
    "Quest Diagnostics Training Facility",
    "NovaCare Complex",
    "BigBear.ai Performance Center",
    "Halas Hall",
    "Detroit Lions Meijer Performance Center",
    "841 Armed Forces Dr, Ashwaubenon",
    "2700 Vikings Circle, Eagan",
    "4400 Falcon Pkwy, Flowery Branch",
    "Bank of America Stadium",
    "5800 Airline Dr, Metairie",
    "AdventHealth Training Center",
    "State Farm Stadium",
    "6100 Owensmouth Ave, Woodland Hills",
    "SAP Performance Facility",
    "Virginia Mason Athletic Center"
]

airports_order = [
    "Buffalo-Niagara International Airport",
    "Miami International Airport",
    "Rhode Island T.F. Green International Airport",
    "Newark Liberty International Airport",
    "Baltimore–Washington International Airport",
    "Cincinnati/Northern Kentucky International Airport",
    "Cleveland Hopkins International Airport",
    "Pittsburgh International Airport",
    "George Bush Intercontinental Airport",
    "Indianapolis International Airport",
    "Jacksonville International Airport",
    "Nashville International Airport",
    "Denver International Airport",
    "Kansas City International Airport",
    "Harry Reid International Airport",
    "Los Angeles International Airport",
    "Dallas/Fort Worth International Airport",
    "Newark Liberty International Airport",
    "Philadelphia International Airport",
    "Washington Dulles International Airport",
    "O'Hare International Airport",
    "Detroit Metropolitan Wayne County Airport",
    "Austin Straubel International Airport",
    "Minneapolis–Saint Paul International Airport",
    "Hartsfield–Jackson Atlanta International Airport",
    "Charlotte Douglas International Airport",
    "Louis Armstrong New Orleans International Airport",
    "Tampa International Airport",
    "Phoenix Sky Harbor International Airport",
    "Los Angeles International Airport",
    "San Jose International Airport",
    "Seattle–Tacoma International Airport"
]

HEADERS = {"User-Agent": "NFL (arya.lum@mail.utoronto.ca)"}

def geocode_nominatim(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    response = requests.get(url, params=params, headers=HEADERS)
    data = response.json()
    if not data:
        return None, None
    return float(data[0]["lat"]), float(data[0]["lon"])

with open(PROJECT_ROOT / "data" / "intermediate" / "coordinates.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "team",
        "stadium", "stadium_lat", "stadium_lon",
        "facility", "facility_lat", "facility_lon",
        "airport", "airport_lat", "airport_lon"
    ])
    for team, stadium, facility, airport in zip(teams_order, stadiums_order, facilities_order, airports_order):
        stadium_lat, stadium_lon = geocode_nominatim(stadium)
        time.sleep(1)
        facility_lat, facility_lon = geocode_nominatim(facility)
        time.sleep(1)
        airport_lat, airport_lon = geocode_nominatim(airport)
        time.sleep(1)
        writer.writerow([
            team,
            stadium, stadium_lat, stadium_lon,
            facility, facility_lat, facility_lon,
            airport, airport_lat, airport_lon
        ])



