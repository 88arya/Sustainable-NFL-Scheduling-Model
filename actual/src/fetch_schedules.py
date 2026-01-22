import os
import time
import csv
import requests
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()  
SPORTSBLAZE_API_KEY = os.getenv("SPORTSBLAZE_API_KEY")

if not SPORTSBLAZE_API_KEY:
    raise RuntimeError("SPORTSBLAZE_API_KEY not set in .env")

SEASONS = range(2021, 2026)
OUTPUT_DIR = "schedules"
REQUEST_DELAY = 0.25 

def _fetch_season_schedule(season: int) -> List[Dict]:
    url = f"https://api.sportsblaze.com/nfl/v1/schedule/season/{season}.json"
    params = {
        "key": SPORTSBLAZE_API_KEY,
        "type": "Regular Season"  
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("games", [])

def _normalize_games(raw_games: List[Dict], season: int) -> List[Dict]:
    normalized = []
    for game in raw_games:
        teams = game.get("teams", {})
        home = teams.get("home", {}).get("name")
        away = teams.get("away", {}).get("name")
        if home and away:
            normalized.append({
                "season": season,
                "home_team": home,
                "away_team": away
            })
    return normalized

def _write_csv(season: int, games: List[Dict]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{season}_schedule.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["season", "home_team", "away_team"])
        writer.writeheader()
        writer.writerows(games)

def fetch_and_save_all_schedules() -> None:
    for season in SEASONS:
        try:
            raw_games = _fetch_season_schedule(season)
            games = _normalize_games(raw_games, season)
            _write_csv(season, games)
            print(f"Saved {len(games)} games for {season}")
        except requests.exceptions.HTTPError as e:
            print(f"Failed to fetch {season} schedule: {e}")
        time.sleep(REQUEST_DELAY)

if __name__ == "__main__":
    fetch_and_save_all_schedules()


