import os
import json
import pandas as pd
from flask import Flask, request, abort
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import joblib

from linebot.v3.webhooks import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, ReplyMessageRequest, PushMessageRequest

# 載入 .env 環境變數
load_dotenv()
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

# LINE SDK 初始化
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(CHANNEL_SECRET)
app = Flask(__name__)

# 載入模型
model_win = joblib.load("models/model_home_win.pkl")
model_spread = joblib.load("models/model_spread.pkl")
model_over = joblib.load("models/model_over.pkl")

# 模擬比賽資料（未來可改為爬蟲動態抓取）
def get_today_games():
    return [
        {"home_team": "Lakers", "away_team": "Warriors", "home_score": 110, "away_score": 105},
        {"home_team": "Celtics", "away_team": "Heat", "home_score": 100, "away_score": 102},
    ]

# AI 推薦產生器
def generate_ai_prediction():
    games = get_today_games()
    msg = f"🏀 AI 賽事預測 ({datetime.now().strftime('%m/%d')})\n\n"
    for g in games:
        X = pd.DataFrame([[g["home_score"], g["away_score"]]], columns=["home_score", "away_score"])
        win = model_win.predict(X)[0]
        spread = model_spread.predict(X)[0]
        ou = model_over.predict(X)[0]

        msg += f"{g['home_team']} vs {g['away_team']}\n"
        msg += f"預測勝方：{'主隊' if win == 1 else '客隊'}\n"
        msg += f"推薦盤口：{'主隊過盤' if spread else '客隊受讓'}\n"
        msg += f"大小分推薦：{'大分' if ou else '小分'}\n\n"
    return msg

# === Flask 路由 ===
@app.route("/")
def home():
    return "✅ LINE AI 推播機器人正常運行中"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook error:", e)
        abort(400)
    return "OK"

@app.route("/test", methods=["GET"])
def test_push():
    msg = generate_ai_prediction()
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=msg)]))
    return "✅ 已手動推播"

# === LINE 指令回覆 ===
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()
    if user_text.startswith("/查詢"):
        reply = generate_ai_prediction()
    else:
        reply = "請輸入 /查詢 查看今日 AI 推薦結果\n或使用 /test 測試推播功能"
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply)]
        )
    )

# === 定時任務 ===
scheduler = BackgroundScheduler()

@scheduler.scheduled_job("cron", minute="0")
def hourly_push():
    try:
        msg = generate_ai_prediction()
        line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=msg)]))
        print("✅ 每小時自動推播成功")
    except Exception as e:
        print("❌ 自動推播錯誤：", e)

scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
