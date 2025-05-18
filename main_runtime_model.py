import os
import json
import pandas as pd
from sklearn.linear_model import LogisticRegression
from dotenv import load_dotenv
from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from proxy.odds_fetcher import get_odds_from_proxy
from proxy.odds_proxy import fetch_oddspedia_soccer

from googletrans import Translator
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, PushMessageRequest, ReplyMessageRequest
from linebot.v3.webhooks.models import CallbackRequest, MessageEvent, TextMessageContent

# === 初始化 ===
load_dotenv()
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
app = Flask(__name__)

# === 動態訓練模型 ===
def train_models():
    nba_path = 'data/nba/nba_history_2023_2024.csv'
    if not os.path.exists(nba_path):
        raise FileNotFoundError(f"找不到資料檔案：{nba_path}")

    nba_df = pd.read_csv(nba_path)
    nba_df['home_win'] = (nba_df['home_score'] > nba_df['away_score']).astype(int)
    nba_df['spread'] = ((nba_df['home_score'] - nba_df['away_score']) > -2.5).astype(int)
    nba_df['over_under'] = ((nba_df['home_score'] + nba_df['away_score']) > 220).astype(int)

    X = nba_df[['home_score', 'away_score']]
    y_win = nba_df['home_win']
    y_spread = nba_df['spread']
    y_over = nba_df['over_under']

    model_win = LogisticRegression().fit(X, y_win)
    model_spread = LogisticRegression().fit(X, y_spread)
    model_over = LogisticRegression().fit(X, y_over)

    return model_win, model_spread, model_over

model_win, model_spread, model_over = train_models()

# === Google 翻譯隊名快取 ===
CACHE_FILE = "team_translation_cache.json"
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        team_name_cache = json.load(f)
else:
    team_name_cache = {}

translator = Translator()

def translate_team_name(name):
    if name in team_name_cache:
        return team_name_cache[name]
    try:
        result = translator.translate(name, src="en", dest="zh-tw")
        team_name_cache[name] = result.text
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(team_name_cache, f, ensure_ascii=False)
        return result.text
    except:
        return name

# 模擬資料（後續會改成即時資料）
def get_games(sport="nba"):
    if sport == "nba":
        return [{"home_team": "Lakers", "away_team": "Warriors", "home_score": 110, "away_score": 105}]
    elif sport == "mlb":
        return [{"home_team": "Yankees", "away_team": "Red Sox", "home_score": 4, "away_score": 6}]
    elif sport == "soccer":
        return [{"home_team": "Liverpool", "away_team": "Man City", "home_score": 2, "away_score": 3}]
    return []

# AI 推薦產生器
def generate_ai_prediction(sport="nba"):
    games = get_games(sport)
    odds_data = get_odds_from_proxy()
    title = {"nba": "🏀 NBA", "mlb": "⚾ MLB", "soccer": "⚽ 足球"}.get(sport, "📊 AI 賽事")
    msg = f"{title} 推薦（{datetime.now().strftime('%m/%d')}）\n\n"

    for g in games:
        X = pd.DataFrame([[g["home_score"], g["away_score"]]], columns=["home_score", "away_score"])
        win = model_win.predict(X)[0]
        spread = model_spread.predict(X)[0]
        ou = model_over.predict(X)[0]

        msg += f"{translate_team_name(g['home_team'])} vs {translate_team_name(g['away_team'])}\n"
        msg += f"預測勝方：{'主隊' if win else '客隊'}\n"
        msg += f"推薦盤口：{'主隊過盤' if spread else '客隊受讓'}\n"
        msg += f"大小分推薦：{'大分' if ou else '小分'}\n"

        for o in odds_data:
            if g["home_team"] in o["match"] and g["away_team"] in o["match"]:
                msg += f"實際賠率：{o['home_odds']} / {o['away_odds']}\n"
                break

        msg += "\n"
    return msg

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_data(as_text=True)
        events = CallbackRequest.from_json(body).events
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                handle_message(event)
    except Exception as e:
        print("Webhook error:", e)
        abort(400)
    return "OK"

def handle_message(event):
    user_text = event.message.text.strip()
    if user_text.startswith("/查詢") or user_text == "/NBA查詢":
        reply = generate_ai_prediction("nba")
    elif user_text == "/MLB查詢":
        reply = generate_ai_prediction("mlb")
    elif user_text == "/足球查詢":
        reply = generate_ai_prediction("soccer")
    else:
        reply = (
            "請輸入以下指令查詢推薦：\n"
            "/查詢 或 /NBA查詢\n"
            "/MLB查詢\n"
            "/足球查詢\n"
            "/test 測試推播"
        )

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply)]
        )
    )

@app.route("/test", methods=["GET"])
def test_push():
    msg = generate_ai_prediction()
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=msg)]))
    return "✅ 測試推播完成"

@app.route("/odds-proxy", methods=["GET"])
def odds_proxy():
    return fetch_oddspedia_soccer()

@app.route("/")
def home():
    return "✅ LINE Bot v3 運作中"

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
