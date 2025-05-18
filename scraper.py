# scraper_sofascore.py
import requests
from bs4 import BeautifulSoup

def get_games_from_sofascore(sport="nba"):
    url_map = {
        "nba": "https://www.sofascore.com/basketball/nba",
        "mlb": "https://www.sofascore.com/baseball/usa/mlb",
        "kbo": "https://www.sofascore.com/baseball/south-korea/kbo",
        "npb": "https://www.sofascore.com/baseball/japan/pro-yakyu-npb",
        "soccer": "https://www.sofascore.com/football"
    }
    url = url_map.get(sport)
    if not url:
        return []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        game_blocks = soup.select("div.eventRow__main")[:5]  # 抓取前五場示意

        games = []
        for block in game_blocks:
            teams = block.select("span.eventRow__name")
            scores = block.select_one("div.eventRow__score")

            if len(teams) == 2 and scores and ":" in scores.text:
                home_team = teams[0].text.strip()
                away_team = teams[1].text.strip()
                home_score, away_score = map(int, scores.text.strip().split(":"))

                games.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_score": home_score,
                    "away_score": away_score
                })
        return games

    except Exception as e:
        print(f"抓取 SofaScore 失敗：{e}")
        return []
