# main_runtime_model_v1_4.py

import os
import json
import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from bs4 import BeautifulSoup
from sklearn.linear_model import LogisticRegression
from googletrans import Translator

from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, PushMessageRequest, ReplyMessageRequest
from linebot.v3.webhooks.models import CallbackRequest, MessageEvent, TextMessageContent

# === 初始化 ===
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
app = Flask(__name__)

# === 模型訓練 ===
def train_models():
    df = pd.read_csv("data/nba/nba_history_2023_2024.csv")
    df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
    df['spread'] = ((df['home_score'] - df['away_score']) > -2.5).astype(int)
    df['over_under'] = ((df['home_score'] + df['away_score']) > 220).astype(int)
    X = df[['home_score', 'away_score']]
    return (
        LogisticRegression().fit(X, df['home_win']),
        LogisticRegression().fit(X, df['spread']),
        LogisticRegression().fit(X, df['over_under']),
    )

model_win, model_spread, model_over = train_models()

# === 翻譯快取 ===
CACHE_FILE = "team_translation_cache.json"
translator = Translator()
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        team_name_cache = json.load(f)
else:
    team_name_cache = {}

def translate_team_name(name):
    if name in team_name_cache:
        return team_name_cache[name]
    try:
        result = translator.translate(name, dest="zh-tw").text
        team_name_cache[name] = result
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(team_name_cache, f, ensure_ascii=False)
        return result
    except:
        return name

# === 賠率抓取 ===
def get_odds_from_proxy():
    try:
        url = "https://sofascore-proxy-production.up.railway.app/odds-proxy"
        res = requests.get(url, timeout=10)
        data = res.json()
        return data["data"] if data.get("status") == "success" else []
    except Exception as e:
        print("賠率抓取錯誤：", e)
        return []

# === SofaScore Proxy 爬蟲 ===
def get_games_from_sofascore(sport="nba"):
    url_map = {
        "nba": "/basketball/nba",
        "mlb": "/baseball/usa/mlb",
        "kbo": "/baseball/south-korea/kbo",
        "npb": "/baseball/japan/pro-yakyu-npb",
        "soccer": "/football"
    }
    url = f"https://sofascore-proxy-production.up.railway.app{url_map.get(sport)}"
    try:
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        blocks = soup.select("div.eventRow__main")
        games = []
        for block in blocks:
            teams = block.select("span.eventRow__name")
            score = block.select_one("div.eventRow__score")
            if len(teams) == 2 and score and ":" in score.text:
                h, a = teams[0].text.strip(), teams[1].text.strip()
                hs, as_ = map(int, score.text.strip().split(":"))
                games.append({"home_team": h, "away_team": a, "home_score": hs, "away_score": as_})
        return games
    except Exception as e:
        print(f"[SofaScore] {sport} 抓取失敗：", e)
        return []

# === 統一 get_games ===
def get_games(sport="nba"):
    return get_games_from_sofascore(sport)

# === AI 推薦產生器 ===
def generate_ai_prediction(sport="nba"):
    games = get_games(sport)
    odds = get_odds_from_proxy()
    emoji = {"nba": "🏀", "mlb": "⚾", "npb": "⚾", "kbo": "⚾", "soccer": "⚽"}
    msg = f"{emoji.get(sport, '📊')} {sport.upper()} 推薦（{datetime.now().strftime('%m/%d')}）\n\n"
    if not games:
        return msg + "今日無比賽數據可供預測。\n"
    for g in games:
        X = pd.DataFrame([[g['home_score'], g['away_score']]], columns=["home_score", "away_score"])
        win = model_win.predict(X)[0]
        spread = model_spread.predict(X)[0]
        ou = model_over.predict(X)[0]
        h = translate_team_name(g["home_team"])
        a = translate_team_name(g["away_team"])
        msg += f"{h} vs {a}\n"
        msg += f"預測勝方：{'主隊' if win else '客隊'}\n"
        msg += f"推薦盤口：{'主隊過盤' if spread else '客隊受讓'}\n"
        msg += f"大小分推薦：{'大分' if ou else '小分'}\n"
        for o in odds:
            if g["home_team"] in o["match"] and g["away_team"] in o["match"]:
                msg += f"實際賠率：{o['home_odds']} / {o['away_odds']}\n"
                break
        msg += "\n"
    return msg

# === LINE Webhook ===
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
    text = event.message.text.strip()
    if text == "/NBA查詢":
        reply = generate_ai_prediction("nba")
    elif text == "/MLB查詢":
        reply = generate_ai_prediction("mlb")
    elif text == "/NPB查詢":
        reply = generate_ai_prediction("npb")
    elif text == "/KBO查詢":
        reply = generate_ai_prediction("kbo")
    elif text == "/足球查詢":
        reply = generate_ai_prediction("soccer")
    else:
        reply = (
            "請輸入以下指令查詢推薦：\n"
            "/NBA查詢\n/MLB查詢\n/NPB查詢\n/KBO查詢\n/足球查詢\n/test 測試推播"
        )
    line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply)]))

@app.route("/test", methods=["GET"])
def test_push():
    msg = generate_ai_prediction("nba")
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=msg)]))
    return "✅ 測試推播完成"

@app.route("/")
def home():
    return "✅ LINE Bot 運作中"

# === 定時推播 ===
scheduler = BackgroundScheduler()

@scheduler.scheduled_job("cron", minute="0")
def hourly_push():
    try:
        msg = generate_ai_prediction("nba")
        line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=msg)]))
        print("✅ 每小時推播成功")
    except Exception as e:
        print("❌ 推播失敗：", e)

scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
