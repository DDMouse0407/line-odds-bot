# main_runtime_model_v1.4.1.py

import os
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, abort
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, PushMessageRequest, ReplyMessageRequest
from linebot.v3.webhooks.models import CallbackRequest, MessageEvent, TextMessageContent
from sklearn.linear_model import LogisticRegression
from googletrans import Translator

# === 初始化 ===
load_dotenv()
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)

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
        translated = translator.translate(name, dest='zh-tw').text
        team_name_cache[name] = translated
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(team_name_cache, f, ensure_ascii=False)
        return translated
    except:
        return name

# === 抓 SofaScore Proxy 比賽資料 ===
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
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        blocks = soup.select("div.eventRow__main")[:5]
        games = []
        for block in blocks:
            teams = block.select("span.eventRow__name")
            scores = block.select_one("div.eventRow__score")
            if len(teams) == 2 and scores and ":" in scores.text:
                home, away = teams[0].text.strip(), teams[1].text.strip()
                hs, as_ = map(int, scores.text.strip().split(":"))
                games.append({
                    "home_team": home, "away_team": away,
                    "home_score": hs, "away_score": as_
                })
        return games
    except Exception as e:
        print(f"抓取 SofaScore Proxy 失敗：{e}")
        return []

# === 賠率抓取 ===
def get_odds_from_proxy():
    try:
        url = "https://line-odds-bot.up.railway.app/odds-proxy"  # ← 請替換成你的正確網址
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["status"] == "success":
            return data["data"]
        else:
            print("賠率 API 回傳非 success 狀態")
            return []
    except Exception as e:
        print("賠率抓取錯誤：", e)
        return []

# === 主邏輯產出 ===
def get_games(sport="nba"):
    return get_games_from_sofascore(sport)

def generate_ai_prediction(sport="nba"):
    games = get_games(sport)
    title = {
        "nba": "🏀 NBA", "mlb": "⚾ MLB", "npb": "⚾ NPB",
        "kbo": "⚾ KBO", "soccer": "⚽ SOCCER"
    }.get(sport, "📊 AI 賽事")
    msg = f"{title} 推薦（{datetime.now().strftime('%m/%d')}）\n\n"

    if not games:
        msg += "今日無比賽數據可供預測。"
        return msg

    odds_data = get_odds_from_proxy()

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
        msg += f"大小分推薦：{'大分' if ou else '小分'}\n"

        for o in odds_data:
            if g["home_team"] in o["match"] and g["away_team"] in o["match"]:
                msg += f"實際賠率：{o['home_odds']} / {o['away_odds']}\n"
                break
        msg += "\n"
    return msg

# === Webhook ===
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
    if text.startswith("/查詢") or text == "/NBA查詢":
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
            "/查詢 或 /NBA查詢\n"
            "/MLB查詢 /NPB查詢 /KBO查詢\n"
            "/足球查詢\n"
            "/test 測試推播"
        )
    line_bot_api.reply_message(ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=reply)]
    ))

# === 推播測試 ===
@app.route("/test", methods=["GET"])
def test_push():
    msg = generate_ai_prediction()
    line_bot_api.push_message(PushMessageRequest(
        to=USER_ID, messages=[TextMessage(text=msg)]
    ))
    return "✅ 測試推播完成"

# === 賠率 API Proxy ===
@app.route("/odds-proxy", methods=["GET"])
def odds_proxy():
    try:
        from proxy.odds_proxy import fetch_oddspedia_soccer
        odds_data = fetch_oddspedia_soccer()
        return {
            "status": "success",
            "data": odds_data
        }
    except Exception as e:
        print("賠率 API 錯誤：", e)
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

# === 其他 ===
@app.route("/")
def home():
    return "✅ LINE Bot 運作中 (V1.4.1)"

# === 定時任務 ===
scheduler = BackgroundScheduler()
@scheduler.scheduled_job("cron", minute="0")
def hourly_push():
    try:
        msg = generate_ai_prediction()
        line_bot_api.push_message(PushMessageRequest(
            to=USER_ID, messages=[TextMessage(text=msg)]
        ))
        print("✅ 每小時推播成功")
    except Exception as e:
        print("❌ 自動推播錯誤：", e)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
