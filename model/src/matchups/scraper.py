from playwright.sync_api import sync_playwright
import os

def scrape_and_save_standings(year=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if year is None:
        while True:
            try:
                year = int(input("Enter the year of the NFL schedule you would like to see (2021 - 2026): "))
                if 2021 <= year <= 2026:
                    break
                else:
                    print("Invalid input. Please enter a year between 2021 and 2026.")
            except ValueError:
                print("Invalid input. Please enter a year between 2021 and 2026.")

    scrape_year = year - 1
    url = f"https://www.nfl.com/standings/division/{scrape_year}/REG"
    teams = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
        page = context.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_function(
            """() => {
                const cell = document.querySelector("table.d3-o-table tbody tr td");
                return cell && cell.innerText.trim().length > 0;
            }""",
            timeout=15000
        )

        for table in page.query_selector_all("table.d3-o-table"):
            for row in table.query_selector_all("tbody tr"):
                team = row.query_selector("td").inner_text().split("\n")[0].strip()
                teams.append(team)

        teams = list(dict.fromkeys(teams))

        context.close()
        browser.close()

    output_path = os.path.join(script_dir, "../../data/intermediate/rankings.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for team in teams:
            f.write(team + "\n")

    return year, teams

if __name__ == "__main__":
    scrape_and_save_standings()















