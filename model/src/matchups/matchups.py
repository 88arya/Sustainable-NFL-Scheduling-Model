from scraper import scrape_and_save_standings
import csv
import os


def generate_matchups(year=None, teams=None):
    if year is None or teams is None:
        year, teams = scrape_and_save_standings(year)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    rankings_path = os.path.join(script_dir, '..', '..', 'data', 'intermediate', 'rankings.txt')

    teamNameToRank = {} 
    with open(rankings_path, 'r') as f:
        for rank, line in enumerate(f, start=1):
            team_name = line.strip()
            if team_name:
                teamNameToRank[team_name] = rank

    missing_teams = [team for team in teams if team not in teamNameToRank]
    if missing_teams:
        raise ValueError(f"The following teams are missing from rankings.txt: {missing_teams}")

    NUM_TEAMS = 32
    m = [[0 for _ in range(NUM_TEAMS)] for _ in range(NUM_TEAMS)]

    AFC_EAST = list(range(0, 4))
    AFC_NORTH = list(range(4, 8))
    AFC_SOUTH = list(range(8, 12))
    AFC_WEST = list(range(12, 16))

    NFC_EAST = list(range(16, 20))
    NFC_NORTH = list(range(20, 24))
    NFC_SOUTH = list(range(24, 28))
    NFC_WEST = list(range(28, 32))

    DIVISIONS = [
        AFC_EAST, AFC_NORTH, AFC_SOUTH, AFC_WEST,
        NFC_EAST, NFC_NORTH, NFC_SOUTH, NFC_WEST
    ]

    for division in DIVISIONS:
        for i in division:
            for j in division:
                if i != j:
                    m[i][j] = 2  

    def div_matchup(div1, div2):
        for i in div1:
            for j in div2:
                m[i][j] = 1
                m[j][i] = 1

    def get_division_for_team(team_idx):
        for div in DIVISIONS:
            if team_idx in div:
                return div
        return None

    def get_divisional_standing(team_idx):
        div = get_division_for_team(team_idx)
        div_sorted = sorted(div, key=lambda x: teamNameToRank[teams[x]])
        return div_sorted.index(team_idx)

    def rank_matchup(div1, div2):
        div1_by_standing = sorted(div1, key=lambda x: get_divisional_standing(x))
        div2_by_standing = sorted(div2, key=lambda x: get_divisional_standing(x))
        for pos in range(4):
            i = div1_by_standing[pos]
            j = div2_by_standing[pos]
            m[i][j] = 1
            m[j][i] = 1

    rOne = (year - 2025) % 3
    rTwo = (year - 2025) % 4

    if rOne == 0:
        div_matchup(AFC_NORTH, AFC_EAST)
        div_matchup(AFC_WEST, AFC_SOUTH)
        div_matchup(NFC_NORTH, NFC_EAST)
        div_matchup(NFC_WEST, NFC_SOUTH)

        rank_matchup(AFC_EAST, AFC_SOUTH)
        rank_matchup(AFC_EAST, AFC_WEST)
        rank_matchup(AFC_NORTH, AFC_SOUTH)
        rank_matchup(AFC_NORTH, AFC_WEST)
        rank_matchup(NFC_EAST, NFC_SOUTH)
        rank_matchup(NFC_EAST, NFC_WEST)
        rank_matchup(NFC_NORTH, NFC_SOUTH)
        rank_matchup(NFC_NORTH, NFC_WEST)
    elif rOne == 1:
        div_matchup(AFC_WEST, AFC_EAST)
        div_matchup(AFC_SOUTH, AFC_NORTH)
        div_matchup(NFC_WEST, NFC_EAST)
        div_matchup(NFC_SOUTH, NFC_NORTH)

        rank_matchup(AFC_EAST, AFC_NORTH)
        rank_matchup(AFC_EAST, AFC_SOUTH)
        rank_matchup(AFC_WEST, AFC_NORTH)
        rank_matchup(AFC_WEST, AFC_SOUTH)
        rank_matchup(NFC_EAST, NFC_NORTH)
        rank_matchup(NFC_EAST, NFC_SOUTH)
        rank_matchup(NFC_WEST, NFC_NORTH)
        rank_matchup(NFC_WEST, NFC_SOUTH)
    elif rOne == 2:
        div_matchup(AFC_SOUTH, AFC_EAST)
        div_matchup(AFC_WEST, AFC_NORTH)
        div_matchup(NFC_SOUTH, NFC_EAST)
        div_matchup(NFC_WEST, NFC_NORTH)

        rank_matchup(AFC_EAST, AFC_NORTH)
        rank_matchup(AFC_EAST, AFC_WEST)
        rank_matchup(AFC_SOUTH, AFC_NORTH)
        rank_matchup(AFC_SOUTH, AFC_WEST)
        rank_matchup(NFC_EAST, NFC_NORTH)
        rank_matchup(NFC_EAST, NFC_WEST)
        rank_matchup(NFC_SOUTH, NFC_NORTH)
        rank_matchup(NFC_SOUTH, NFC_WEST)

    if rTwo == 0:
        div_matchup(NFC_SOUTH, AFC_EAST)
        div_matchup(NFC_NORTH, AFC_NORTH)
        div_matchup(NFC_WEST, AFC_SOUTH)
        div_matchup(NFC_EAST, AFC_WEST)

        rank_matchup(AFC_EAST, NFC_EAST)
        rank_matchup(AFC_NORTH, NFC_WEST)
        rank_matchup(AFC_SOUTH, NFC_SOUTH)
        rank_matchup(AFC_WEST, NFC_NORTH)
    elif rTwo == 1:
        div_matchup(NFC_NORTH, AFC_EAST)
        div_matchup(NFC_SOUTH, AFC_NORTH)
        div_matchup(NFC_EAST, AFC_SOUTH)
        div_matchup(NFC_WEST, AFC_WEST)

        rank_matchup(AFC_EAST, NFC_WEST)
        rank_matchup(AFC_NORTH, NFC_EAST)
        rank_matchup(AFC_SOUTH, NFC_NORTH)
        rank_matchup(AFC_WEST, NFC_SOUTH)
    elif rTwo == 2:
        div_matchup(NFC_EAST, AFC_EAST)
        div_matchup(NFC_WEST, AFC_NORTH)
        div_matchup(NFC_SOUTH, AFC_SOUTH)
        div_matchup(NFC_NORTH, AFC_WEST)

        rank_matchup(AFC_EAST, NFC_SOUTH)
        rank_matchup(AFC_NORTH, NFC_NORTH)
        rank_matchup(AFC_SOUTH, NFC_WEST)
        rank_matchup(AFC_WEST, NFC_EAST)
    elif rTwo == 3:
        div_matchup(NFC_WEST, AFC_EAST)
        div_matchup(NFC_EAST, AFC_NORTH)
        div_matchup(NFC_NORTH, AFC_SOUTH)
        div_matchup(NFC_SOUTH, AFC_WEST)

        rank_matchup(AFC_EAST, NFC_NORTH)
        rank_matchup(AFC_NORTH, NFC_SOUTH)
        rank_matchup(AFC_SOUTH, NFC_EAST)
        rank_matchup(AFC_WEST, NFC_WEST)

    output_path = os.path.join(script_dir, '..', '..', 'data', 'matchups', 'matrix_m.csv')
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([''] + teams)
        for i, row in enumerate(m):
            writer.writerow([teams[i]] + row)

    return year, teams, m

if __name__ == "__main__":
    generate_matchups()



