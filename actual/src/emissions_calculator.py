import csv
import os

BUS_EMISSION_RATE = 4.256  # kg CO2/km
PLANE_EMISSION_RATE = 12.3  # kg CO2/km

BUS_THRESHOLD = 500


def load_single_team_distances(filepath):
    distances = {}
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = row['team']
            distance = float(row['distance_km'])
            distances[team] = distance
    return distances


def load_team_pair_distances(filepath):
    distances = {}
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'away_team' in row:
                away_team = row['away_team']
                home_team = row['home_team']
            else:
                away_team = row['team_i']
                home_team = row['team_j']
            distance = float(row['distance_km'])
            distances[(away_team, home_team)] = distance
    return distances


def load_schedule(filepath):
    games = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            games.append({
                'home_team': row['home_team'],
                'away_team': row['away_team']
            })
    return games


def calculate_home_team_emissions(home_team, facility_to_stadium):
    distance = facility_to_stadium.get(home_team, 0)
    total_distance = distance * 2
    emissions = total_distance * BUS_EMISSION_RATE
    return emissions


def calculate_away_team_emissions(away_team, home_team,
                                   facility_to_away_stadium,
                                   facility_to_home_airport,
                                   home_airport_to_away_airport,
                                   away_stadium_to_away_airport):

    direct_distance = facility_to_away_stadium.get((away_team, home_team), 0)

    if direct_distance <= BUS_THRESHOLD:

        total_distance = direct_distance * 2
        emissions = total_distance * BUS_EMISSION_RATE

    else:
    
        leg1_distance = facility_to_home_airport.get(away_team, 0)
        leg1_emissions = leg1_distance * BUS_EMISSION_RATE
   
        leg2_distance = home_airport_to_away_airport.get((away_team, home_team), 0)
        leg2_emissions = leg2_distance * PLANE_EMISSION_RATE

        leg3_distance = away_stadium_to_away_airport.get(home_team, 0)
        leg3_emissions = leg3_distance * BUS_EMISSION_RATE

        one_way_emissions = leg1_emissions + leg2_emissions + leg3_emissions

        emissions = one_way_emissions * 2

    return emissions


def calculate_season_emissions(year, base_path):

    facility_to_stadium = load_single_team_distances(
        os.path.join(base_path, 'data', 'HomeFacility_HomeStadium.csv')
    )
    facility_to_away_stadium = load_team_pair_distances(
        os.path.join(base_path, 'data', 'HomeFacility_AwayStadium.csv')
    )
    facility_to_home_airport = load_single_team_distances(
        os.path.join(base_path, 'data', 'HomeFacility_HomeAirport.csv')
    )
    home_airport_to_away_airport = load_team_pair_distances(
        os.path.join(base_path, 'data', 'HomeAirport_AwayAirport.csv')
    )
    stadium_to_airport = load_single_team_distances(
        os.path.join(base_path, 'data', 'HomeStadium_HomeAirport.csv')
    )

    schedule_path = os.path.join(base_path, 'schedules', f'{year}_schedule.csv')
    games = load_schedule(schedule_path)

    total_emissions = 0.0

    for game in games:
        home_team = game['home_team']
        away_team = game['away_team']

        home_emissions = calculate_home_team_emissions(
            home_team, facility_to_stadium
        )

        away_emissions = calculate_away_team_emissions(
            away_team, home_team,
            facility_to_away_stadium,
            facility_to_home_airport,
            home_airport_to_away_airport,
            stadium_to_airport
        )

        total_emissions += home_emissions + away_emissions

    return total_emissions


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(script_dir)
    emissions_dir = os.path.join(base_path, 'emissions')

    os.makedirs(emissions_dir, exist_ok=True)

    for year in range(2021, 2026):
        total_emissions = calculate_season_emissions(year, base_path)

        output_path = os.path.join(emissions_dir, f'{year}_emissions.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"{total_emissions:.2f} kg CO2\n")
            f.write(f"{total_emissions / 1000:.2f} metric tonnes CO2\n")

        print(f"{year}: {total_emissions:.2f} kg CO2")


if __name__ == '__main__':
    main()

