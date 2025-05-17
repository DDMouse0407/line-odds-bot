# scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

BASE_URLS = {
    "soccer": "https://oddspedia.com/football",
    "nba": "https://oddspedia.com/basketball/usa/nba",
    "mlb": "https://oddspedia.com/baseball/usa/mlb",
    "npb": "https://oddspedia.com/baseball/japan/npb",
    "kbo": "https://oddspedia.com/baseball/south-korea/kbo-league"
}


def fetch_matches(sport_name, url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        events = soup.select("a.eventRow")[:5]  # 限制前5場
        results = []

        for event in events:
            teams = event.select(".teamName")
            odds = event.select(".oddsCell__odd")
            time_tag = event.select_one(".date")

            if len(teams) >= 2 and odds:
                match_time = time_tag.text.strip() if time_tag else "未知時間"
                team1 = teams[0].text.strip()
                team2 = teams[1].text.strip()
                main_odd = odds[0].text.strip()

                results.append({
                    "time": match_time,
                    "team1": team1,
                    "team2": team2,
                    "odd": main_odd
                })

        return results
    except Exception as e:
        print(f"❌ 無法抓取 {sport_name}：", e)
        return []


def get_all_odds():
    now = datetime.now().strftime("%m/%d %H:%M")
    result_text = f"📊 賠率分析更新時間：{now}\n\n"

    # ⚽ 足球
    soccer_matches = fetch_matches("足球", BASE_URLS["soccer"])
    result_text += "⚽ 各國足球\n"
    for match in soccer_matches:
        result_text += f"🕓 {match['time']}｜{match['team1']} vs {match['team2']}\n推薦：{match['team1']}（賠率：{match['odd']}）\n\n"

    # 🏀 NBA
    nba_matches = fetch_matches("NBA", BASE_URLS["nba"])
    result_text += "🏀 美國籃球\n"
    for match in nba_matches:
        result_text += f"🕓 {match['time']}｜{match['team1']} vs {match['team2']}\n推薦：{match['team1']}（賠率：{match['odd']}）\n\n"

    # ⚾ 台韓日美棒球
    result_text += "⚾ 台韓日美棒球\n"

    for key, name in [("kbo", "韓國 KBO"), ("npb", "日本 NPB"), ("mlb", "美國 MLB")]:
        matches = fetch_matches(name, BASE_URLS[key])
        for match in matches:
            result_text += f"🕓 {match['time']}｜{match['team1']} vs {match['team2']}（{name}）\n推薦：{match['team1']}（賠率：{match['odd']}）\n\n"

    return result_text
