import requests

def get_odds_from_proxy():
    try:
        proxy_url = "https://line-odds-bot.up.railway.app/odds-proxy"
        response = requests.get(proxy_url, timeout=10)
        data = response.json()
        if data["status"] == "success":
            return data["data"]
        else:
            return []
    except Exception as e:
        print("賠率抓取錯誤：", e)
        return []
