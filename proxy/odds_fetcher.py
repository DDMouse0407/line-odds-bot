import requests

def get_odds_from_proxy():
    try:
        proxy_url = "https://你的專案名稱.up.railway.app/odds-proxy"  # 替換為你的網址
        response = requests.get(proxy_url, timeout=10)
        data = response.json()
        if data["status"] == "success":
            return data["data"]
        else:
            return []
    except Exception as e:
        print("賠率抓取錯誤：", e)
        return []
