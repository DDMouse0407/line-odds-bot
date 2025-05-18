# injury_parser.py
import requests
from bs4 import BeautifulSoup

def get_rotowire_injuries(sport="nba"):
    url_map = {
        "nba": "https://www.rotowire.com/basketball/injury-report.php",
        "mlb": "https://www.rotowire.com/baseball/injury-report.php"
    }

    url = url_map.get(sport)
    if not url:
        return {}

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", class_="injury-table")
    injury_data = {}

    if not table:
        return {}

    rows = table.find_all("tr")[1:]  # skip header

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        team = cols[0].text.strip()
        player = cols[1].text.strip()
        position = cols[2].text.strip()
        status = cols[3].text.strip()
        notes = cols[4].text.strip()

        if team not in injury_data:
            injury_data[team] = []

        injury_data[team].append({
            "player": player,
            "position": position,
            "status": status,
            "notes": notes
        })

    return injury_data
