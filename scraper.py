import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 範例：抓取 NBA 比賽賠率（Oddspedia）
def fetch_odds_nba():
    url = "https://oddspedia.com/basketball/usa/nba"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        for match in soup.select(".eventRow"):
            try:
                teams = match.select_one(".eventCell__name").get_text(separator=" vs ").strip()
                start_time = match.select_one(".eventCell__time").text.strip()

                odds_cells = match.select(".bookmakerItem__odds")
                if len(odds_cells) >= 2:
                    home_odds = odds_cells[0].text.strip()
                    away_odds = odds_cells[1].text.strip()
                else:
                    continue

                results.append({
                    "teams": teams,
                    "start_time": start_time,
                    "home_odds": home_odds,
                    "away_odds": away_odds,
                    "recommend": "主勝" if float(home_odds) < float(away_odds) else "客勝",
                })

            except Exception:
                continue

        return results

    except Exception as e:
        print("❌ 抓取失敗：", str(e))
        return []
