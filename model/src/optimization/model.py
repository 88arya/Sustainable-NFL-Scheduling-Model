import os
import sys
import pandas as pd
from pulp import (
    LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, LpStatus, value
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'matchups'))

BUS_EMISSION_RATE = 4.256  # kg CO2/km
PLANE_EMISSION_RATE = 12.3  # kg CO2/km

BUS_ONLY_THRESHOLD = 500  # km

NUM_TEAMS = 32
NUM_WEEKS = 18
NUM_SLOTS = 3  
GAMES_PER_WEEK = 16  
BYE_WEEK_START = 5
BYE_WEEK_END = 14

TEAMS = [
    "Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets",
    "Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans",
    "Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
    "Dallas Cowboys", "New York Giants", "Philadelphia Eagles", "Washington Commanders",
    "Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings",
    "Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers",
    "Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks"
]

TEAM_IDX = {team: i for i, team in enumerate(TEAMS)}

STADIUM_SHARING_PAIRS = [
    ("Los Angeles Rams", "Los Angeles Chargers"),
    ("New York Giants", "New York Jets")
]

DIVISIONS = {
    "AFC_EAST": [0, 1, 2, 3],
    "AFC_NORTH": [4, 5, 6, 7],
    "AFC_SOUTH": [8, 9, 10, 11],
    "AFC_WEST": [12, 13, 14, 15],
    "NFC_EAST": [16, 17, 18, 19],
    "NFC_NORTH": [20, 21, 22, 23],
    "NFC_SOUTH": [24, 25, 26, 27],
    "NFC_WEST": [28, 29, 30, 31]
}

def get_data_path(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "../../data", filename)


def load_matchup_matrix():
    path = get_data_path("matchups/matrix_m.csv")
    df = pd.read_csv(path, index_col=0)

    matrix = {}
    for i, team_i in enumerate(TEAMS):
        for j, team_j in enumerate(TEAMS):
            matrix[(i, j)] = int(df.loc[team_i, team_j])

    return matrix


def load_distance_matrix(filename):
    path = get_data_path(f"distances/{filename}")
    df = pd.read_csv(path)

    distances = {}

    if 'away_team' in df.columns:
        for _, row in df.iterrows():
            i = TEAM_IDX[row['away_team']]
            j = TEAM_IDX[row['home_team']]
            distances[(i, j)] = row['distance_km']
    elif 'team_i' in df.columns:
        for _, row in df.iterrows():
            i = TEAM_IDX[row['team_i']]
            j = TEAM_IDX[row['team_j']]
            distances[(i, j)] = row['distance_km']
    else:
        for _, row in df.iterrows():
            i = TEAM_IDX[row['team']]
            distances[i] = row['distance_km']

    return distances


def load_all_distances():
    return {
        'facility_to_stadium': load_distance_matrix('HomeFacility_HomeStadium.csv'),
        'facility_to_airport': load_distance_matrix('HomeFacility_HomeAirport.csv'),
        'stadium_to_airport': load_distance_matrix('HomeStadium_HomeAirport.csv'),
        'facility_to_away_stadium': load_distance_matrix('HomeFacility_AwayStadium.csv'),
        'airport_to_airport': load_distance_matrix('HomeAirport_AwayAirport.csv')
    }

def calculate_travel_emissions(distances, team_i, team_j, is_home_game):
    if is_home_game:
        facility_stadium_dist = distances['facility_to_stadium'].get(team_i, 0)
        return 2 * facility_stadium_dist * BUS_EMISSION_RATE
    else:
        facility_to_away = distances['facility_to_away_stadium'].get((team_i, team_j), 0)

        if facility_to_away < BUS_ONLY_THRESHOLD:
            return 2 * facility_to_away * BUS_EMISSION_RATE
        else:
            facility_to_airport = distances['facility_to_airport'].get(team_i, 0)
            airport_to_airport = distances['airport_to_airport'].get((team_i, team_j), 0)
            opponent_airport_to_stadium = distances['stadium_to_airport'].get(team_j, 0)

            outbound = (
                facility_to_airport * BUS_EMISSION_RATE +
                airport_to_airport * PLANE_EMISSION_RATE +
                opponent_airport_to_stadium * BUS_EMISSION_RATE
            )
            return 2 * outbound


def precompute_game_emissions(distances, matchup_matrix):
    emissions = {}

    for i in range(NUM_TEAMS):
        for j in range(NUM_TEAMS):
            if i != j and matchup_matrix.get((i, j), 0) > 0:
                emissions[(i, j, True)] = calculate_travel_emissions(distances, i, j, True)
                emissions[(i, j, False)] = calculate_travel_emissions(distances, i, j, False)

    return emissions


def calculate_paired_away_emissions(distances, team_i, opp1, opp2):
    facility_to_airport = distances['facility_to_airport'].get(team_i, 0)
    home_to_opp1_airport = distances['airport_to_airport'].get((team_i, opp1), 0)
    opp1_airport_to_stadium = distances['stadium_to_airport'].get(opp1, 0)
    opp1_to_opp2_airport = distances['airport_to_airport'].get((opp1, opp2), 0)
    opp2_airport_to_stadium = distances['stadium_to_airport'].get(opp2, 0)
    opp2_to_home_airport = distances['airport_to_airport'].get((team_i, opp2), 0)

    emissions = (
        facility_to_airport * BUS_EMISSION_RATE +
        home_to_opp1_airport * PLANE_EMISSION_RATE +
        2 * opp1_airport_to_stadium * BUS_EMISSION_RATE +
        opp1_to_opp2_airport * PLANE_EMISSION_RATE +
        2 * opp2_airport_to_stadium * BUS_EMISSION_RATE +
        opp2_to_home_airport * PLANE_EMISSION_RATE +
        facility_to_airport * BUS_EMISSION_RATE
    )

    return emissions


def calculate_separate_away_emissions(distances, team_i, opp1, opp2):
    sunday_emissions = calculate_travel_emissions(distances, team_i, opp1, False)
    thursday_emissions = calculate_travel_emissions(distances, team_i, opp2, False)
    return sunday_emissions + thursday_emissions


def precompute_average_paired_savings(distances, matchup_matrix):
    avg_savings = {}

    for i in range(NUM_TEAMS):
        total_savings = 0
        count = 0

        for opp1 in range(NUM_TEAMS):
            if i == opp1 or matchup_matrix.get((i, opp1), 0) == 0:
                continue

            for opp2 in range(NUM_TEAMS):
                if i == opp2 or matchup_matrix.get((i, opp2), 0) == 0:
                    continue

                paired = calculate_paired_away_emissions(distances, i, opp1, opp2)
                separate = calculate_separate_away_emissions(distances, i, opp1, opp2)
                total_savings += separate - paired
                count += 1

        avg_savings[i] = total_savings / count if count > 0 else 0

    return avg_savings

def create_nfl_schedule_model():
    """Create the NFL schedule optimization model."""
    print("Loading data...")
    matchup_matrix = load_matchup_matrix()
    distances = load_all_distances()
    game_emissions = precompute_game_emissions(distances, matchup_matrix)
    avg_paired_savings = precompute_average_paired_savings(distances, matchup_matrix)

    print("Creating optimization model...")
    model = LpProblem("NFL_Schedule_Optimization",LpMinimize)

    # Decision Variables
    x = {}
    for i in range(NUM_TEAMS):
        for j in range(NUM_TEAMS):
            if i != j and matchup_matrix.get((i, j), 0) > 0:
                for w in range(NUM_WEEKS):
                    for s in range(NUM_SLOTS):
                        x[(i, j, w, s)] = LpVariable(f"x_{i}_{j}_{w}_{s}", cat=LpBinary)

    h = {}
    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS):
            h[(i, w)] = LpVariable(f"h_{i}_{w}", cat=LpBinary)

    a = {}
    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS):
            a[(i, w)] = LpVariable(f"a_{i}_{w}", cat=LpBinary)

    bye = {}
    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS):
            bye[(i, w)] = LpVariable(f"bye_{i}_{w}", cat=LpBinary)

    y = {}
    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS - 1): 
            y[(i, w)] = LpVariable(f"y_{i}_{w}", cat=LpBinary)

    print("Setting up objective function...")

    emission_terms = []
    for (i, j, w, s), var in x.items():
        away_emissions = game_emissions.get((i, j, False), 0)
        home_emissions = game_emissions.get((j, i, True), 0)
        emission_terms.append((away_emissions + home_emissions) * var)

    savings_terms = []
    for (i, w), var in y.items():
        savings = avg_paired_savings.get(i, 0)
        savings_terms.append(savings * var)

    model += lpSum(emission_terms) - lpSum(savings_terms), "Total_CO2_Emissions"

    print("Adding constraints...")

    for i in range(NUM_TEAMS):
        for j in range(i + 1, NUM_TEAMS):
            matchup_value = matchup_matrix.get((i, j), 0)

            if matchup_value == 2:
                model += (
                    lpSum(x[(i, j, w, s)] for w in range(NUM_WEEKS)
                          for s in range(NUM_SLOTS) if (i, j, w, s) in x) == 1,
                    f"Divisional_i_away_{i}_{j}"
                )
                model += (
                    lpSum(x[(j, i, w, s)] for w in range(NUM_WEEKS)
                          for s in range(NUM_SLOTS) if (j, i, w, s) in x) == 1,
                    f"Divisional_j_away_{i}_{j}"
                )
            elif matchup_value == 1:
                games_ij = [x[(i, j, w, s)] for w in range(NUM_WEEKS)
                           for s in range(NUM_SLOTS) if (i, j, w, s) in x]
                games_ji = [x[(j, i, w, s)] for w in range(NUM_WEEKS)
                           for s in range(NUM_SLOTS) if (j, i, w, s) in x]
                model += lpSum(games_ij + games_ji) == 1, f"NonDiv_matchup_{i}_{j}"

    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS):
            model += h[(i, w)] + a[(i, w)] + bye[(i, w)] == 1, f"One_activity_{i}_{w}"

    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS):
            home_games = [x[(j, i, w, s)] for j in range(NUM_TEAMS)
                         for s in range(NUM_SLOTS) if (j, i, w, s) in x]
            away_games = [x[(i, j, w, s)] for j in range(NUM_TEAMS)
                         for s in range(NUM_SLOTS) if (i, j, w, s) in x]

            if home_games:
                model += lpSum(home_games) == h[(i, w)], f"Link_home_{i}_{w}"
            else:
                model += h[(i, w)] == 0, f"No_home_possible_{i}_{w}"

            if away_games:
                model += lpSum(away_games) == a[(i, w)], f"Link_away_{i}_{w}"
            else:
                model += a[(i, w)] == 0, f"No_away_possible_{i}_{w}"

    for i in range(NUM_TEAMS):
        model += (
            lpSum(h[(i, w)] + a[(i, w)] for w in range(NUM_WEEKS)) == 17,
            f"Total_games_{i}"
        )

    for i in range(NUM_TEAMS):
        total_home = lpSum(h[(i, w)] for w in range(NUM_WEEKS))
        model += total_home >= 8, f"Min_home_{i}"
        model += total_home <= 9, f"Max_home_{i}"

    for i in range(NUM_TEAMS):
        model += lpSum(bye[(i, w)] for w in range(NUM_WEEKS)) == 1, f"One_bye_{i}"
        for w in range(NUM_WEEKS):
            if w < BYE_WEEK_START - 1 or w > BYE_WEEK_END - 1:
                model += bye[(i, w)] == 0, f"No_bye_week_{i}_{w}"

    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS - 3):
            model += lpSum(h[(i, w + k)] for k in range(4)) <= 3, f"Max_consec_home_{i}_{w}"
            model += lpSum(a[(i, w + k)] for k in range(4)) <= 3, f"Max_consec_away_{i}_{w}"

    for _, div_teams in DIVISIONS.items():
        for idx, i in enumerate(div_teams):
            for j in div_teams[idx + 1:]:
                for w in range(NUM_WEEKS - 1):
                    games_w = []
                    games_w1 = []
                    for s in range(NUM_SLOTS):
                        if (i, j, w, s) in x:
                            games_w.append(x[(i, j, w, s)])
                        if (j, i, w, s) in x:
                            games_w.append(x[(j, i, w, s)])
                        if (i, j, w + 1, s) in x:
                            games_w1.append(x[(i, j, w + 1, s)])
                        if (j, i, w + 1, s) in x:
                            games_w1.append(x[(j, i, w + 1, s)])

                    if games_w and games_w1:
                        model += lpSum(games_w) + lpSum(games_w1) <= 1, f"No_consec_div_{i}_{j}_{w}"

    for team_a, team_b in STADIUM_SHARING_PAIRS:
        idx_a = TEAM_IDX[team_a]
        idx_b = TEAM_IDX[team_b]

        for w in range(NUM_WEEKS):
            for s in range(NUM_SLOTS):
                home_a = [x[(j, idx_a, w, s)] for j in range(NUM_TEAMS) if (j, idx_a, w, s) in x]
                home_b = [x[(j, idx_b, w, s)] for j in range(NUM_TEAMS) if (j, idx_b, w, s) in x]

                playing_each_other = []
                if (idx_b, idx_a, w, s) in x:
                    playing_each_other.append(x[(idx_b, idx_a, w, s)])
                if (idx_a, idx_b, w, s) in x:
                    playing_each_other.append(x[(idx_a, idx_b, w, s)])

                if home_a and home_b:
                    if playing_each_other:
                        model += (
                            lpSum(home_a) + lpSum(home_b) <= 1 + lpSum(playing_each_other),
                            f"Stadium_share_{idx_a}_{idx_b}_{w}_{s}"
                        )
                    else:
                        model += lpSum(home_a) + lpSum(home_b) <= 1, f"Stadium_share_{idx_a}_{idx_b}_{w}_{s}"

    for w in range(NUM_WEEKS):
        thursday_games = [x[(i, j, w, 0)] for i in range(NUM_TEAMS)
                         for j in range(NUM_TEAMS) if (i, j, w, 0) in x]
        if thursday_games:
            model += lpSum(thursday_games) == 1, f"Thursday_game_count_{w}"

        monday_games = [x[(i, j, w, 2)] for i in range(NUM_TEAMS)
                       for j in range(NUM_TEAMS) if (i, j, w, 2) in x]
        if monday_games:
            model += lpSum(monday_games) == 1, f"Monday_game_count_{w}"

    for w in range(NUM_WEEKS):
        all_games = [x[(i, j, w, s)] for i in range(NUM_TEAMS)
                    for j in range(NUM_TEAMS) for s in range(NUM_SLOTS)
                    if (i, j, w, s) in x]
        total_byes = lpSum(bye[(i, w)] for i in range(NUM_TEAMS))

        if all_games:
            model += 2 * lpSum(all_games) + total_byes == 32, f"Games_per_week_{w}"

    v = {}
    for w in range(1, NUM_WEEKS): 
        v[w] = LpVariable(f"v_{w}", cat=LpBinary)

    for i in range(NUM_TEAMS):
        for w in range(1, NUM_WEEKS): 
            thursday_away = [x[(i, j, w, 0)] for j in range(NUM_TEAMS) if (i, j, w, 0) in x]
            sunday_away_prev = [x[(i, j, w - 1, 1)] for j in range(NUM_TEAMS) if (i, j, w - 1, 1) in x]

            if thursday_away and sunday_away_prev:
                model += (
                    lpSum(thursday_away) <= lpSum(sunday_away_prev) + v[w],
                    f"Thursday_requires_Sunday_away_{i}_{w}"
                )
            elif thursday_away:
                model += lpSum(thursday_away) <= v[w], f"No_Thursday_away_{i}_{w}"

    model += lpSum(v[w] for w in range(1, NUM_WEEKS)) <= 1, 

    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS - 1):
            sunday_away = [x[(i, j, w, 1)] for j in range(NUM_TEAMS) if (i, j, w, 1) in x]
            thursday_away_next = [x[(i, j, w + 1, 0)] for j in range(NUM_TEAMS) if (i, j, w + 1, 0) in x]

            if sunday_away and thursday_away_next:
                model += y[(i, w)] <= lpSum(sunday_away), f"Y_link_sunday_{i}_{w}"
                model += y[(i, w)] <= lpSum(thursday_away_next), f"Y_link_thursday_{i}_{w}"
                model += (
                    y[(i, w)] >= lpSum(sunday_away) + lpSum(thursday_away_next) - 1,
                    f"Y_link_both_{i}_{w}"
                )
            else:
                model += y[(i, w)] == 0, f"Y_zero_{i}_{w}"

    print(f"Model created with {len(model.constraints)} constraints")

    variables = {'x': x, 'h': h, 'a': a, 'bye': bye, 'y': y}
    return model, variables, matchup_matrix

def extract_schedule(variables):
    """Extract the schedule from solved model variables."""
    x = variables['x']
    bye_vars = variables['bye']

    slot_names = {0: 'Thursday', 1: 'Sunday', 2: 'Monday'}
    schedule = {team: [] for team in TEAMS}

    for w in range(NUM_WEEKS):
        week_num = w + 1

        for i in range(NUM_TEAMS):
            team_name = TEAMS[i]

            if value(bye_vars[(i, w)]) > 0.5:
                schedule[team_name].append({
                    'week': week_num, 'opponent': 'BYE', 'home_away': '-', 'slot': '-'
                })
                continue

            found_game = False
            for j in range(NUM_TEAMS):
                for s in range(NUM_SLOTS):
                    if (i, j, w, s) in x and value(x[(i, j, w, s)]) > 0.5:
                        schedule[team_name].append({
                            'week': week_num, 'opponent': TEAMS[j],
                            'home_away': 'Away', 'slot': slot_names[s]
                        })
                        found_game = True
                        break
                    if (j, i, w, s) in x and value(x[(j, i, w, s)]) > 0.5:
                        schedule[team_name].append({
                            'week': week_num, 'opponent': TEAMS[j],
                            'home_away': 'Home', 'slot': slot_names[s]
                        })
                        found_game = True
                        break
                if found_game:
                    break

            if not found_game:
                schedule[team_name].append({
                    'week': week_num, 'opponent': 'ERROR', 'home_away': '-', 'slot': '-'
                })

    return schedule


def print_schedule(schedule):
    for team, games in schedule.items():
        print(f"\n{'='*60}")
        print(f"{team}")
        print(f"{'='*60}")
        print(f"{'Week':<6} {'Opponent':<25} {'H/A':<6} {'Day'}")
        print(f"{'-'*60}")
        for game in games:
            print(f"{game['week']:<6} {game['opponent']:<25} {game['home_away']:<6} {game['slot']}")


def save_schedule_to_csv(schedule, filepath):
    """Save the schedule to a CSV file."""
    rows = []
    for team, games in schedule.items():
        for game in games:
            rows.append({
                'team': team, 'week': game['week'], 'opponent': game['opponent'],
                'home_away': game['home_away'], 'slot': game['slot']
            })

    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False)
    print(f"Schedule saved to {filepath}")


def save_emissions_to_txt(total_emissions, paired_trips, filepath):
    with open(filepath, 'w') as f:
        f.write(f"{total_emissions:.2f} kg CO2\n")
        f.write(f"{total_emissions / 1000:.2f} metric tons CO2\n\n")
    print(f"Emissions saved to {filepath}")


def calculate_total_emissions(schedule, distances):
    total_emissions = 0
    paired_trips_count = 0

    for team, games in schedule.items():
        team_idx = TEAM_IDX[team]

        paired_sunday_weeks = set()
        paired_thursday_weeks = set()

        for i, game in enumerate(games):
            if game['opponent'] == 'BYE' or game['opponent'] == 'ERROR':
                continue
            if game['home_away'] != 'Away' or game['slot'] != 'Sunday':
                continue

            week = game['week']
            if i + 1 < len(games):
                next_game = games[i + 1]
                if (next_game['opponent'] != 'BYE' and
                    next_game['opponent'] != 'ERROR' and
                    next_game['home_away'] == 'Away' and
                    next_game['slot'] == 'Thursday' and
                    next_game['week'] == week + 1):
                    paired_sunday_weeks.add(week)
                    paired_thursday_weeks.add(week + 1)

        for i, game in enumerate(games):
            if game['opponent'] == 'BYE' or game['opponent'] == 'ERROR':
                continue

            opponent_idx = TEAM_IDX[game['opponent']]
            is_home = game['home_away'] == 'Home'
            week = game['week']

            if is_home:
                emissions = calculate_travel_emissions(distances, team_idx, opponent_idx, True)
                total_emissions += emissions
            elif week in paired_sunday_weeks:
                next_game = games[i + 1]
                opp1 = opponent_idx
                opp2 = TEAM_IDX[next_game['opponent']]
                paired_emissions = calculate_paired_away_emissions(distances, team_idx, opp1, opp2)
                total_emissions += paired_emissions
                paired_trips_count += 1
            elif week in paired_thursday_weeks:
                pass
            else:
                emissions = calculate_travel_emissions(distances, team_idx, opponent_idx, False)
                total_emissions += emissions

    print(f"Paired Sunday-Thursday trips: {paired_trips_count}")
    return total_emissions, paired_trips_count

def solve_schedule(time_limit=3600, mip_gap=0.005):
    """Solve the NFL schedule optimization problem."""
    model, variables, _ = create_nfl_schedule_model()

    print("\nSolving model...")
    print(f"Time limit: {time_limit} seconds")
    print(f"MIP gap: {mip_gap * 100}%")

    from pulp import PULP_CBC_CMD
    solver = PULP_CBC_CMD(timeLimit=time_limit, gapRel=mip_gap, msg=True)
    model.solve(solver)

    print(f"\nSolution status: {LpStatus[model.status]}")

    if model.status == 1:  
        print(f"Objective value (Total CO2 emissions): {value(model.objective):.2f} kg")

        schedule = extract_schedule(variables)

        distances = load_all_distances()
        total_emissions, paired_trips = calculate_total_emissions(schedule, distances)
        print(f"Verified total emissions: {total_emissions:.2f} kg")

        return schedule, total_emissions, paired_trips
    else:
        print("No optimal solution found.")
        return None, None, None


def get_output_path(year, filename):
    """Get absolute path to output file for a specific year."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, f"../../output/{year}", filename)


def run_all_years(years=None, time_limit=3600, mip_gap=0.005):
    from matchups import generate_matchups

    if years is None:
        years = list(range(2021, 2027))  

    print("=" * 60)
    print("NFL Schedule Optimization - Carbon Emissions Minimization")
    print("=" * 60)
    print(f"\nProcessing years: {years}")
    print("=" * 60)

    results = {}

    for year in years:
        print(f"\n{'='*60}")
        print(f"Processing {year} NFL Season")
        print(f"{'='*60}")

        print(f"\nStep 1: Generating matchups for {year}")
        print("-" * 60)
        _, teams, _ = generate_matchups(year=year)

        print(f"\nStep 2: Optimizing schedule for {year}")
        print("-" * 60)
        schedule, total_emissions, paired_trips = solve_schedule(
            time_limit=time_limit, mip_gap=mip_gap
        )

        if schedule is not None:
            schedule_path = get_output_path(year, f"{year}_schedule.csv")
            save_schedule_to_csv(schedule, schedule_path)

            emissions_path = get_output_path(year, f"{year}_emissions.txt")
            save_emissions_to_txt(total_emissions, paired_trips, emissions_path)

            results[year] = {
                'total_emissions': total_emissions,
                'paired_trips': paired_trips
            }

            print(f"\n{year} completed successfully!")
        else:
            print(f"\n{year} failed to find optimal solution.")
            results[year] = None

    print("\n" + "=" * 60)
    print("SUMMARY - All Years")
    print("=" * 60)
    for year, result in results.items():
        if result:
            print(f"{year}: {result['total_emissions']:.2f} kg CO2 "
                  f"({result['total_emissions']/1000:.2f} metric tons)")
        else:
            print(f"{year}: Failed")

    return results


if __name__ == "__main__":
    run_all_years()
