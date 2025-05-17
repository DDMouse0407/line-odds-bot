import os
import json
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, PushMessageRequest, ReplyMessageRequest

# ======== 環境與初始化 ========
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")

app = Flask(__name__)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(CHANNEL_SECRET)

# ======== 路由與 Webhook ========
@app.route("/")
def home():
    return "✅ LINE Bot 已啟動"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook Error:", e)
        abort(400)

    return "OK"

@app.route("/test", methods=["GET"])
def test_push():
    text = generate_odds_report()
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=text)]))
    return "✅ 測試訊息已推播"

# ======== 訊息處理指令 ========
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    if text.startswith("/查詢"):
        keyword = text.replace("/查詢", "").strip()
        reply_text = query_odds(keyword)
    else:
        reply_text = "✅ 指令成功\n/test（手動推播）\n/查詢 [隊名或聯賽名]"
    line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply_text)]))

# ======== 賠率分析與推播 ========
def generate_odds_report():
    now = datetime.now().strftime("%m/%d %H:%M")
    text = f"📊 賠率分析更新時間：{now}\n\n"

    # 模擬分類與判斷（可改成抓 Oddspedia）
    games = [
        {
            "type": "⚽ 各國足球",
            "time": "18:00",
            "match": "利物浦 vs 曼城",
            "recommend": "利物浦 +1.5",
            "analysis": "主隊近期4連勝，客隊有主力中場傷缺，讓分盤偏深，可能誘導買曼城"
        },
        {
            "type": "🏀 美國籃球",
            "time": "20:30",
            "match": "湖人 vs 勇士",
            "recommend": "大分 228.5",
            "analysis": "兩隊對戰常爆分，近期皆偏高比分，盤口大分水位異常上升"
        },
        {
            "type": "⚾ 台韓日美棒球",
            "time": "17:00",
            "match": "阪神虎 vs 巨人",
            "recommend": "巨人 -1.5",
            "analysis": "阪神王牌投手缺陣，巨人近期3連勝，盤口讓分明顯，有利巨人"
        }
    ]

    categorized = {"⚽ 各國足球": [], "🏀 美國籃球": [], "⚾ 台韓日美棒球": []}
    for g in games:
        line = f"🕓 {g['time']}｜{g['match']}\n推薦：{g['recommend']}\n分析：{g['analysis']}\n"
        categorized[g['type']].append(line)

    for k, v in categorized.items():
        text += f"{k}\n" + "\n".join(v) + "\n"

    return text

# ======== 關鍵字查詢功能 ========
def query_odds(keyword):
    all_games = {
        "利物浦": "⚽ 利物浦 vs 曼城\n推薦：利物浦 +1.5\n分析：主隊4連勝＋曼城主力傷缺",
        "湖人": "🏀 湖人 vs 勇士\n推薦：大分 228.5\n分析：雙方對戰常爆分",
        "阪神": "⚾ 阪神虎 vs 巨人\n推薦：巨人 -1.5\n分析：阪神缺主投＋巨人三連勝"
    }
    result = []
    for key, val in all_games.items():
        if keyword in key:
            result.append(val)
    return "\n\n".join(result) if result else f"❌ 查無「{keyword}」相關賽事"

# ======== 自動推播排程 ========
scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', minute='0')  # 每小時整點推播
def auto_push():
    try:
        text = generate_odds_report()
        line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=text)]))
        print("✅ 自動推播成功")
    except Exception as e:
        print("❌ 自動推播失敗：", e)

scheduler.start()

# ======== 啟動應用 ========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
