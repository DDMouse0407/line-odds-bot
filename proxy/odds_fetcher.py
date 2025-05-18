import requests

def get_odds_from_proxy():
    try:
        proxy_url = "https://line-odds-bot.up.railway.app/odds-proxy"  # 改為你 LINE Bot 專案的 URL
        response = requests.get(proxy_url, timeout=10)

        # 確認是 JSON 格式
        if response.headers.get("Content-Type", "").startswith("application/json"):
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", [])
            else:
                print("賠率 API 回傳非 success 狀態")
                return []
        else:
            print("賠率抓取錯誤：非 JSON 回傳")
            print("實際內容：", response.text[:200])
            return []

    except Exception as e:
        print("賠率抓取錯誤：", e)
        return []
