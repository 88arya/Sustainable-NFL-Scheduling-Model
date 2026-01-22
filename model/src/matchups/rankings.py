import os

teams_order = [
    "Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets",
    "Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans",
    "Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
    "Dallas Cowboys", "New York Giants", "Philadelphia Eagles", "Washington Commanders",
    "Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings",
    "Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers",
    "Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks"
]

def generate_team_ranks():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rankings_path = os.path.join(script_dir, "../../data/intermediate/rankings.txt")
    with open(rankings_path, "r", encoding="utf-8") as f:
        standings = [line.strip() for line in f if line.strip()]

    team_to_rank = {team: rank + 1 for rank, team in enumerate(standings)}
    teamRanks = [team_to_rank[team] for team in teams_order]

    for i in range(len(teamRanks)):
        division_index = i // 4
        teamRanks[i] = teamRanks[i] - (division_index * 4)

    return teamRanks








