
import requests
from bs4 import BeautifulSoup

def fetch_odds(sport):
    url_map = {
        'nba': 'https://oddspedia.com/basketball/usa/nba',
        'mlb': 'https://oddspedia.com/baseball/usa/mlb',
        'soccer': 'https://oddspedia.com/football'
    }

    url = url_map.get(sport.lower())
    if not url:
        return []

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    games = []

    for match in soup.select('div.eventRow'):
        try:
            teams = match.select_one('.eventCell__name').text.strip()
            odds = match.select('.bookmaker-area .odds-value')
            home_odds = odds[0].text if len(odds) > 0 else "-"
            away_odds = odds[1].text if len(odds) > 1 else "-"

            games.append({
                'teams': teams,
                'home_odds': home_odds,
                'away_odds': away_odds
            })
        except Exception:
            continue

    return games

# 範例使用
if __name__ == "__main__":
    nba_data = fetch_odds("nba")
    for game in nba_data[:3]:
        print(game)
