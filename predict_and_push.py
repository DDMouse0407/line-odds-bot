import joblib
import pandas as pd
from datetime import datetime
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, PushMessageRequest
import os

# 載入環境變數
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

# 初始化 LINE Messaging API
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)

# 載入模型
model_win = joblib.load("models/model_home_win.pkl")
model_spread = joblib.load("models/model_spread.pkl")
model_over = joblib.load("models/model_over.pkl")

# 模擬今日比賽（可改為真實爬蟲資料）
today_games = [
    {
        "home_team": "Lakers",
        "away_team": "Warriors",
        "home_score": 110,
        "away_score": 105
    },
    {
        "home_team": "Celtics",
        "away_team": "Heat",
        "home_score": 100,
        "away_score": 102
    }
]

# 產生預測推播內容
def generate_predictions(games):
    message = f"📊 AI 賽事預測 ({datetime.now().strftime('%m/%d')})\n\n"
    for game in games:
        X = pd.DataFrame([[game["home_score"], game["away_score"]]], columns=["home_score", "away_score"])
        win = model_win.predict(X)[0]
        spread = model_spread.predict(X)[0]
        ou = model_over.predict(X)[0]

        message += f"{game['home_team']} vs {game['away_team']}\n"
        message += f"預測勝方：{'主隊' if win == 1 else '客隊'}\n"
        message += f"推薦盤口：{'主隊過盤' if spread else '客隊受讓'}\n"
        message += f"大小分推薦：{'大分' if ou else '小分'}\n\n"
    return message

# 發送推播
def push_prediction():
    text = generate_predictions(today_games)
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=text)]))
    print("✅ 已推播預測內容")

# 若直接執行此腳本，立即推播
if __name__ == "__main__":
    push_prediction()
