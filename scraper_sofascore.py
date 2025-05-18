import requests
from bs4 import BeautifulSoup

def get_games_from_sofascore(sport="nba"):
    url_map = {
        "nba": "/basketball/nba",
        "mlb": "/baseball/usa/mlb",
        "kbo": "/baseball/south-korea/kbo",
        "npb": "/baseball/japan/pro-yakyu-npb",
        "soccer": "/football"
    }

    base_url = "https://sofascore-proxy-production.up.railway.app"
    path = url_map.get(sport)
    if not path:
        return []

    full_url = f"{base_url}{path}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(full_url, headers=headers, timeout=10)
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
        print(f"抓取 SofaScore Proxy 失敗：{e}")
        return []
