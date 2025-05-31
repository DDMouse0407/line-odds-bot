# main_runtime_model_v1.5.py

import os
import requests
import pandas as pd
from flask import Flask, request, abort
from bs4 import BeautifulSoup
from datetime import datetime
from linebot.v3 import WebhookHandler, Configuration, ApiClient
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import CallbackRequest

# 初始化 Flask
app = Flask(__name__)

# LINE Bot 初始化
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_bot_api = MessagingApi(ApiClient(configuration))

# 模擬模型
class DummyModel:
    def predict(self, X):
        return [1 if X["home_score"].iloc[0] > X["away_score"].iloc[0] else 0]

model_win = DummyModel()
model_spread = DummyModel()
model_over = DummyModel()

def translate_team_name(name):
    return name

# Cookie 抓取用於 SofaScore
COOKIE_HEADER = '__gads=ID=6d4e4b28213372a8:T=1748704119:RT=1748704119:S=ALNI_MY2Ef2UFsHQsXqFIp1Rj5wF0hLIrA; __gpi=UID=00001109dce1d89a:T=1748704119:RT=1748704119:S=ALNI_MZcHhDCcrZl_oYhxbbdEl0XCTQiNA; __awl=2.1748704121.5-f51ad020095d690ad6f99ed2002de39a-6763652d617369612d6561737431-3; _ga=GA1.1.1206071790.1748704119; _ga_HNQ9P9MGZR=GS2.1.s1748704118$o1$g0$t1748704233$j35$l0$h0; _gcl_au=1.1.1432398338.1748704119'

# 抓 SofaScore 比賽資料
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
        "User-Agent": "Mozilla/5.0",
        "Cookie": COOKIE_HEADER
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        game_blocks = soup.select("div.eventRow__main")[:5]

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
        print("抓取 SofaScore 失敗：", e)
        return []

# 推薦邏輯
@app.route("/predict", methods=["GET"])
def predict():
    sport = request.args.get("sport", "nba")
    games = get_games_from_sofascore(sport)
    title = {"nba": "🏀 NBA", "mlb": "⚾ MLB", "soccer": "⚽ 足球"}.get(sport, "📊 AI 賽事")
    msg = f"{title} 推薦（{datetime.now().strftime('%m/%d')}）\n\n"

    if not games:
        msg += "今日無比賽數據可供預測。"
        return msg

    for g in games:
        X = pd.DataFrame([[g["home_score"], g["away_score"]]], columns=["home_score", "away_score"])
        win = model_win.predict(X)[0]
        spread = model_spread.predict(X)[0]
        ou = model_over.predict(X)[0]

        home = translate_team_name(g["home_team"])
        away = translate_team_name(g["away_team"])

        msg += f"{home} vs {away}\n"
        msg += f"預測勝方：{'主隊' if win else '客隊'}\n"
        msg += f"推薦盤口：{'主隊過盤' if spread else '客隊受讓'}\n"
        msg += f"大小分推薦：{'大分' if ou else '小分'}\n\n"

    return msg

# LINE Webhook 路由
@app.route("/webhook", methods=['POST'])
def webhook():
    try:
        body = request.data.decode("utf-8")
        events = CallbackRequest.from_json(body).events
        for event in events:
            if event.message.type == "text" and event.message.text == "/test":
                result = predict()
                with ApiClient(configuration) as api_client:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=result)]
                        )
                    )
        return "OK"
    except Exception as e:
        print("Webhook 錯誤：", e)
        abort(400)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
