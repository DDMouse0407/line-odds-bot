import requests
from bs4 import BeautifulSoup

def fetch_oddspedia_soccer():
    url = "https://oddspedia.com/football"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        matches = []
        for item in soup.select(".eventRow"):
            teams = item.select_one(".name").text.strip()
            time = item.select_one(".time").text.strip()
            odds = item.select(".odds")
            if len(odds) >= 2:
                match = {
                    "match": teams,
                    "time": time,
                    "home_odds": odds[0].text.strip(),
                    "away_odds": odds[1].text.strip()
                }
                matches.append(match)

        return {"status": "success", "data": matches[:5]}

    except Exception as e:
        return {"status": "error", "message": str(e)}
