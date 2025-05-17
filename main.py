# ========= 1. 套件載入 =========
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

# ========= 2. Flask 初始化 =========
app = Flask(__name__)

# ========= 3. 載入環境變數 =========
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")

# ========= 4. 初始化 LINE BOT v3 SDK =========
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(CHANNEL_SECRET)

# ========= 5. 路由設定 =========

@app.route("/")
def home():
    return "✅ LINE Bot 全功能啟動中（v3 SDK）"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("❌ Webhook Error:", e)
        abort(400)

    return "OK"

@app.route("/test", methods=["GET"])
def test_push():
    text = generate_odds_report()
    message = TextMessage(text=text)
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[message]))
    return "✅ 已手動推播測試內容"

# ========= 6. LINE 訊息處理 =========

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    if text.startswith("/查詢"):
        query = text.replace("/查詢", "").strip()
        reply_text = query_odds(query)
    else:
        reply_text = "✅ 指令成功！目前支援：\n/test（手動推播）\n/查詢 [隊伍或聯賽]"

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )

# ========= 7. 推播邏輯（分析假資料） =========

def generate_odds_report():
    try:
        now = datetime.now().strftime("%m/%d %H:%M")
        text = f"📊 賠率分析更新時間：{now}\n\n"

        text += "⚽ 各國足球\n"
        text += "🕓 18:00｜利物浦 vs 曼城\n推薦：利物浦 +1.5\n分析：主隊近期連勝，客隊傷兵多\n\n"

        text += "🏀 美國籃球\n"
        text += "🕓 20:30｜湖人 vs 勇士\n推薦：大分 228.5\n分析：兩隊對戰常爆分 + 防守鬆散\n\n"

        text += "⚾ 台韓日美棒球\n"
        text += "🕓 17:00｜阪神虎 vs 巨人\n推薦：巨人 -1.5\n分析：主投ERA極低 + 主場優勢明顯\n\n"

        return text
    except Exception as e:
        return f"❌ 賠率分析錯誤：{str(e)}"

def query_odds(keyword):
    if "湖人" in keyword:
        return "🏀 湖人賽事推薦：\n🕓 20:30｜湖人 vs 勇士\n推薦：大分 228.5\n分析：高得分趨勢 + 對戰歷史爆分"
    return f"❌ 查無 {keyword} 相關資料"

# ========= 8. 定時推播排程器 =========

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', minute='0')  # 每小時整點推播
def auto_push():
    try:
        text = generate_odds_report()
        message = TextMessage(text=text)
        line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[message]))
        print("✅ 自動推播完成")
    except Exception as e:
        print("❌ 自動推播失敗：", e)

scheduler.start()

# ========= 9. 執行入口 =========

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
